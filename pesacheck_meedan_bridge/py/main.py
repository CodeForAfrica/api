import json
import sys

import lxml.html  # nosec B410
import requests
import sentry_sdk
import settings
from check_api import post_to_check
from database import PesacheckDatabase, PesacheckFeed


def extract_summary(description):
    # Ghost posts store the plain-text excerpt (the fact-check summary). Legacy
    # Medium rows stored full HTML, where the summary preceded the first <figure>.
    if not description or not description.strip():
        return None
    tree = lxml.html.fromstring(description)
    figures = tree.xpath("//figure")
    if figures and figures[0].getprevious() is not None:
        summary_text = figures[0].getprevious().text_content()
    else:
        summary_text = tree.text_content()
    return summary_text.strip() if summary_text else None


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


def fetch_from_pesacheck():
    url = f"{settings.PESACHECK_GHOST_URL.rstrip('/')}/ghost/api/content/posts/"
    params = {
        "key": settings.PESACHECK_GHOST_CONTENT_API_KEY,
        "limit": settings.PESACHECK_GHOST_POSTS_LIMIT,
        "order": "published_at desc",
        "include": "tags,authors",
        "fields": "id,title,url,excerpt,custom_excerpt,feature_image,published_at",
    }
    headers = {"Accept-Version": "v5.0"}
    response = requests.get(url, params=params, headers=headers, timeout=60)
    if response.status_code != 200:
        raise Exception(
            f"An Error Occurred fetching data from pesacheck: {response.text}"
        )
    return [parse_ghost_post(post) for post in response.json().get("posts") or []]


def store_in_database(feed, db):
    db.insert_pesacheck_feed(feed)
    return feed


def post_to_check_and_update(feed, db):
    categories = json.loads(feed.categories)
    codes = [
        language_codes[language.lower()]
        for language in categories
        if language.lower() in language_codes
    ]
    language = "en" if not codes else codes[0]
    claim_description = feed.title
    summary = extract_summary(feed.description) or "Not Found"
    input_data = {
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
    res = post_to_check(input_data)
    if res:
        feed.check_project_media_id = (
            res["data"].get("createProjectMedia").get("project_media").get("id")
        )
        feed.check_full_url = (
            res["data"].get("createProjectMedia").get("project_media").get("full_url")
        )
        feed.claim_description_id = (
            res["data"]
            .get("createProjectMedia")
            .get("project_media")
            .get("claim_description")
            .get("fact_check")
            .get("id")
        )
        feed.status = "Completed"
        db.update_pesacheck_feed(feed.guid, feed)
        return feed


def main(db):
    success_posts = []
    try:
        unsent_data = db.get_pending_pesacheck_feeds()
        if unsent_data:
            for pending in unsent_data:
                try:
                    posted = post_to_check_and_update(pending, db=db)
                    if posted:
                        success_posts.append(posted)
                except Exception as exception:
                    sentry_sdk.capture_exception(exception)
        from_pesacheck = fetch_from_pesacheck()
        if from_pesacheck:
            for _, item in enumerate(from_pesacheck):
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
                    posted = post_to_check_and_update(feed, db=db)
                    if posted:
                        success_posts.append(posted)
                except Exception as exception:
                    sentry_sdk.capture_exception(exception)
    except Exception as e:
        sentry_sdk.capture_exception(e)
    finally:
        sentry_sdk.capture_message(
            f"Posted {len(success_posts)} PesaCheck article(s) to Check: "
            f"{[post.link for post in success_posts]}"
        )


if __name__ == "__main__":
    try:
        db = PesacheckDatabase()
        if not db:
            sentry_sdk.capture_message("Unable to connect to database")
            sys.exit()
        main(db=db)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        sys.exit()
