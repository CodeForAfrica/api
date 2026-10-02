import json
import sys
from datetime import UTC, datetime

import lxml.html  # nosec B410
import requests
import sentry_sdk
import settings
from check_api import DuplicateFactCheckError, post_to_check
from database import PesacheckDatabase, PesacheckFeed
from provider_ghost import language_from_categories
from providers import get_provider


def extract_summary(feed):
    # Providers store a plain-text summary. Legacy Medium rows stored full
    # HTML, where the summary preceded the first <figure>.
    if feed.source != "medium":
        return feed.description.strip() or None
    tree = lxml.html.fromstring(feed.description)
    figures = tree.xpath("//figure")
    if len(figures) == 0 or figures[0].getprevious() is None:
        return None
    summary_text = figures[0].getprevious().text_content()
    return summary_text.strip() if summary_text else None


def get_checkpoint(db, source=None):
    pub_dates = []
    for pub_date in db.get_pub_dates(source):
        try:
            parsed = datetime.fromisoformat(pub_date)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            # Legacy Medium rows stored "2024-11-18 23:19:22" (UTC, unmarked);
            # without this they can't be compared with the others.
            parsed = parsed.replace(tzinfo=UTC)
        pub_dates.append(parsed)
    return max(pub_dates) if pub_dates else None


def store_in_database(feed, db):
    db.insert_pesacheck_feed(feed)
    return feed


def build_check_input(feed):
    categories = json.loads(feed.categories)
    # Rows stored before the language column fall back to the tag names.
    language = feed.language or language_from_categories(categories) or "en"
    claim_description = feed.title
    summary = extract_summary(feed) or "Not Found"
    return {
        "media_type": "Blank",
        "channel": 1,
        "set_tags": categories,
        "set_status": "verified",
        "set_claim_description": claim_description,
        "title": feed.title,
        "summary": summary,
        "url": feed.link,
        "language": language,
        "publish_report": True,
    }


def mark_terminal(feed, db, status):
    """Record a terminal status without losing the outcome it describes.

    The caller is about to raise the exception this status explains; a failure
    here must not replace it, or a known duplicate would look like a row whose
    outcome could not be recorded.
    """
    feed.status = status
    try:
        db.update_pesacheck_feed_status(feed.guid, status, expected_status="Posting")
    except Exception as exception:
        sentry_sdk.capture_exception(exception)


def post_to_check_and_update(feed, db):
    # Build the request first: a failure here means nothing was sent, so the row
    # must stay "Pending" rather than be marked as maybe-posted.
    input_data = build_check_input(feed)
    # Claim the row before posting: it marks the row as maybe-posted so a failed
    # run doesn't re-post it, and it stops an overlapping run posting it twice.
    if not db.claim_pending_feed(feed.guid):
        return None
    try:
        res = post_to_check(input_data)
    except DuplicateFactCheckError:
        # Check already has this fact-check, so retrying it every run would
        # fail forever. Mark it terminally instead.
        mark_terminal(feed, db, "Duplicate")
        raise
    except requests.RequestException:
        # e.g. a timeout: Check may still have created the item, so leave the
        # row as "Posting" rather than risk a duplicate.
        raise
    except Exception:
        # Check rejected the mutation, so nothing was created.
        mark_terminal(feed, db, "Pending")
        raise
    # post_to_check() has validated the response, so from here on the item
    # exists in Check: a failure to record it leaves the row as "Posting".
    project_media = res["data"]["createProjectMedia"]["project_media"]
    feed.check_project_media_id = project_media.get("id")
    feed.check_full_url = project_media.get("full_url")
    feed.claim_description_id = project_media["claim_description"]["fact_check"]["id"]
    feed.status = "Completed"
    db.update_pesacheck_feed(feed.guid, feed, expected_status="Posting")
    return feed


def count_phrase(count):
    """Shared wording so the run's messages can't drift apart."""
    return f"{count} PesaCheck article(s)"


def post_and_record(feed, db, success_posts, duplicates):
    """Post one stored article, recording the outcome for the run summary."""
    try:
        posted = post_to_check_and_update(feed, db=db)
        if posted is not None:
            success_posts.append(posted.link)
    except DuplicateFactCheckError:
        duplicates.append(feed.link)
    except Exception as exception:
        sentry_sdk.capture_exception(exception)


def main(db):
    success_posts = []
    duplicates = []
    try:
        unreconciled = db.get_pesacheck_feeds_by_status("Posting")
        if unreconciled:
            sentry_sdk.capture_message(
                f"{count_phrase(len(unreconciled))} may have been posted to "
                "Check without being recorded: "
                f"{[feed.link for feed in unreconciled]}",
                level="warning",
            )
        for pending in db.get_pesacheck_feeds_by_status("Pending"):
            post_and_record(pending, db, success_posts, duplicates)
        provider = get_provider(settings.PESACHECK_PROVIDER)
        # On a provider's first run, carry on from wherever the previous one
        # stopped: the same fact-checks exist in both CMSes, and re-posting
        # them would create duplicate published reports in Check rather than
        # being rejected (Check's signature covers the URL, which differs).
        since = get_checkpoint(db, provider.name) or get_checkpoint(db)
        from_pesacheck = provider.fetch(
            since=since,
            limit=settings.PESACHECK_POSTS_LIMIT,
            max_articles=settings.PESACHECK_MAX_ARTICLES,
        )
        # Providers return oldest first, so the checkpoint never moves past an
        # unstored article.
        for post in from_pesacheck:
            try:
                article = provider.parse(post)
            except Exception as exception:
                # A malformed post is skipped: holding the checkpoint behind it
                # would block every later article indefinitely.
                sentry_sdk.capture_exception(exception)
                continue
            try:
                if db.feed_exists(article.guid):
                    continue
                feed = PesacheckFeed(
                    title=article.title,
                    pubDate=article.published_at,
                    author=article.author,
                    guid=article.guid,
                    link=article.url,
                    categories=json.dumps(article.categories),
                    thumbnail=article.thumbnail,
                    description=article.summary,
                    status="Pending",
                    check_project_media_id="",
                    check_full_url="",
                    claim_description_id="",
                    source=provider.name,
                    language=article.language,
                )
                store_in_database(feed, db=db)
            except Exception as exception:
                # The article could not be stored, so stop here: storing a newer
                # one would advance the checkpoint past this one for good. The
                # next run starts again from the current checkpoint.
                sentry_sdk.capture_exception(exception)
                break
            # The article is stored, so a failure here is retried next run.
            post_and_record(feed, db, success_posts, duplicates)
    except Exception as e:
        # Re-raised so that the process exits non-zero and cron/monitoring can
        # see that the whole run failed.
        sentry_sdk.capture_exception(e)
        raise
    finally:
        message = f"Posted {count_phrase(len(success_posts))} to Check: {success_posts}"
        if duplicates:
            message += (
                f". Skipped {count_phrase(len(duplicates))} "
                f"Check already has: {duplicates}"
            )
        sentry_sdk.capture_message(message)


if __name__ == "__main__":
    try:
        main(db=PesacheckDatabase())
    except Exception as e:
        sentry_sdk.capture_exception(e)
        sys.exit(1)
