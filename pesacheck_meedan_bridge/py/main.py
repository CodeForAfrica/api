import json
import sys
from datetime import UTC, datetime

import lxml.html  # nosec B410
import requests
import sentry_sdk
import settings
from check_api import post_to_check
from database import PesacheckDatabase, PesacheckFeed


def is_ghost_feed(feed):
    # Legacy Medium rows use the post URL as guid; Ghost rows use the post id.
    return not feed.guid.startswith("http")


def extract_summary(feed):
    # Ghost rows store the plain-text excerpt, which is the fact-check summary.
    if is_ghost_feed(feed):
        return feed.description.strip() or None
    # Legacy Medium rows stored full HTML, where the summary preceded the first
    # <figure>.
    tree = lxml.html.fromstring(feed.description)
    figures = tree.xpath("//figure")
    if len(figures) == 0 or figures[0].getprevious() is None:
        return None
    summary_text = figures[0].getprevious().text_content()
    return summary_text.strip() if summary_text else None


# Identify the bridge instead of defaulting to "python-requests/x.y.z", which
# Cloudflare challenges in front of pesacheck.org. Kept separate from
# py/VERSION, which isn't packaged into the pex.
USER_AGENT = "PesaCheckMeedanBridge/1.0 (+https://pesacheck.org)"

language_codes = {
    "english": "en",
    "french": "fr",
    "oromo": "om",
    "afaan": "om",
    "afaan oromoo": "om",
    "swahili": "sw",
    "kiswahili": "sw",
    "amharic": "am",
    "somali": "so",
    "somaaliga": "so",
    "tigrinya": "ti",
    "arabic": "ar",
}


def parse_ghost_post(post):
    # Internal Ghost tags (e.g. #hash-tags) are for site organisation only.
    tags = [
        tag["name"]
        for tag in post.get("tags") or []
        if tag.get("visibility") == "public"
    ]
    authors = [author["name"] for author in post.get("authors") or []]
    return {
        "title": post["title"],
        "pubDate": post.get("published_at") or "",
        "author": ", ".join(authors),
        "guid": post["id"],
        "link": post["url"],
        "thumbnail": post.get("feature_image") or "",
        "description": (
            post.get("custom_excerpt") or post.get("excerpt") or ""
        ).strip(),
        "categories": tags,
    }


def get_checkpoint(db):
    pub_dates = []
    for pub_date in db.get_ghost_pub_dates():
        try:
            pub_dates.append(datetime.fromisoformat(pub_date))
        except ValueError:
            continue
    return max(pub_dates) if pub_dates else None


def fetch_from_pesacheck(since=None):
    # Without a checkpoint (first run against Ghost), only fetch the newest
    # page instead of backfilling PesaCheck's entire archive.
    url = f"{settings.PESACHECK_URL.rstrip('/')}/ghost/api/content/posts/"
    params = {
        "key": settings.PESACHECK_GHOST_CONTENT_API_KEY,
        "limit": settings.PESACHECK_GHOST_POSTS_LIMIT,
        "order": "published_at desc",
        "include": "tags,authors",
        "fields": "id,title,url,excerpt,custom_excerpt,feature_image,published_at",
    }
    if since:
        since_utc = since.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
        params["filter"] = f"published_at:>='{since_utc}'"
    headers = {"Accept-Version": "v5.0", "User-Agent": USER_AGENT}
    posts = []
    page = 1
    while page:
        params["page"] = page
        response = requests.get(url, params=params, headers=headers, timeout=60)
        if response.status_code != 200:
            raise Exception(
                f"An Error Occurred fetching data from pesacheck: {response.text}"
            )
        data = response.json()
        posts.extend(data.get("posts") or [])
        pagination = (data.get("meta") or {}).get("pagination") or {}
        page = pagination.get("next") if since else None
    return posts


def store_in_database(feed, db):
    db.insert_pesacheck_feed(feed)
    return feed


def build_check_input(feed):
    categories = json.loads(feed.categories)
    codes = [
        language_codes[language.lower()]
        for language in categories
        if language.lower() in language_codes
    ]
    language = "en" if not codes else codes[0]
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


def post_to_check_and_update(feed, db):
    # Build the request first: a failure here means nothing was sent, so the row
    # must stay "Pending" rather than be marked as maybe-posted.
    input_data = build_check_input(feed)
    # Mark the row before posting so that, if the result cannot be recorded, the
    # row is not re-posted on the next run and is flagged for reconciliation.
    db.update_pesacheck_feed_status(feed.guid, "Posting")
    try:
        res = post_to_check(input_data)
    except requests.RequestException:
        # e.g. a timeout: Check may still have created the item, so leave the
        # row as "Posting" rather than risk a duplicate.
        raise
    except Exception:
        # Check rejected the mutation, so nothing was created.
        db.update_pesacheck_feed_status(feed.guid, "Pending")
        raise
    # post_to_check() has validated the response, so from here on the item
    # exists in Check: a failure to record it leaves the row as "Posting".
    project_media = res["data"]["createProjectMedia"]["project_media"]
    feed.check_project_media_id = project_media.get("id")
    feed.check_full_url = project_media.get("full_url")
    feed.claim_description_id = project_media["claim_description"]["fact_check"]["id"]
    feed.status = "Completed"
    db.update_pesacheck_feed(feed.guid, feed)
    return feed


def main(db):
    success_posts = []
    try:
        unreconciled = db.get_pesacheck_feeds_by_status("Posting")
        if unreconciled:
            sentry_sdk.capture_message(
                f"{len(unreconciled)} PesaCheck article(s) may have been posted to "
                f"Check without being recorded: {[feed.link for feed in unreconciled]}",
                level="warning",
            )
        for pending in db.get_pesacheck_feeds_by_status("Pending"):
            try:
                success_posts.append(post_to_check_and_update(pending, db=db))
            except Exception as exception:
                sentry_sdk.capture_exception(exception)
        from_pesacheck = fetch_from_pesacheck(since=get_checkpoint(db))
        # Oldest first, so the checkpoint never moves past an unstored article.
        for post in reversed(from_pesacheck):
            try:
                item = parse_ghost_post(post)
            except Exception as exception:
                # A malformed post is skipped: holding the checkpoint behind it
                # would block every later article indefinitely.
                sentry_sdk.capture_exception(exception)
                continue
            try:
                if db.feed_exists(item["guid"]):
                    continue
                feed = PesacheckFeed(
                    title=item["title"],
                    pubDate=item["pubDate"],
                    author=item["author"],
                    guid=item["guid"],
                    link=item["link"],
                    categories=json.dumps(item["categories"]),
                    thumbnail=item["thumbnail"],
                    description=item["description"],
                    status="Pending",
                    check_project_media_id="",
                    check_full_url="",
                    claim_description_id="",
                )
                store_in_database(feed, db=db)
            except Exception as exception:
                # The article could not be stored, so stop here: storing a newer
                # one would advance the checkpoint past this one for good. The
                # next run starts again from the current checkpoint.
                sentry_sdk.capture_exception(exception)
                break
            try:
                # The article is stored, so a failure here is retried next run.
                success_posts.append(post_to_check_and_update(feed, db=db))
            except Exception as exception:
                sentry_sdk.capture_exception(exception)
    except Exception as e:
        # Re-raised so that the process exits non-zero and cron/monitoring can
        # see that the whole run failed.
        sentry_sdk.capture_exception(e)
        raise
    finally:
        sentry_sdk.capture_message(
            f"Posted {len(success_posts)} PesaCheck article(s) to Check: "
            f"{[post.link for post in success_posts]}"
        )


if __name__ == "__main__":
    try:
        main(db=PesacheckDatabase())
    except Exception as e:
        sentry_sdk.capture_exception(e)
        sys.exit(1)
