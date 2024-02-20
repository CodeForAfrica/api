import json
import re
import sys

import requests
import sentry_sdk
import settings
from check_api import post_to_check
from database import PesacheckDatabase, PesacheckFeed


def remove_html_tags(input_string):
    return re.sub(r"<[^>]*>", "", input_string)


language_codes = {
    "english": "en",
    "french": "fr",
    "oromo": "om",
    "swahili": "sw",
    "amharic": "am",
    "somali": "so",
    "tigrinya": "ti",
    "arabic": "ar",
}


def fetch_from_pesacheck():
    url = "https://api.rss2json.com/v1/api.json"
    feed_url = settings.PESACHECK_URL
    params = {
        "rss_url": feed_url,
        "api_key": settings.PESACHECK_RSS2JSON_API_KEY,
        "count": 10,
        "order_by": "pubDate",
    }
    response = requests.get(url, params=params, timeout=60)
    if response.status_code == 200:
        return response.json().get("items") or []
    raise Exception("An Error Occurred fetching data from pesacheck")


def store_in_database(feed, db):
    db.insert_pesacheck_feed(feed)
    return feed


def post_to_check_and_update(feed, db):
    categories = json.loads(feed.categories)
    codes = [
        language_codes[language.lower()]
        for language in feed.categories
        if language.lower() in language_codes
    ]
    language = "en" if not codes else codes[0]
    input_data = {
        "media_type": "Blank",
        "channel": 1,
        "set_tags": categories,
        "set_status": "verified",
        "set_claim_description": f"""{remove_html_tags(feed.description)}""",
        "title": f"""{remove_html_tags(feed.title)}""",
        "summary": f"""{remove_html_tags(feed.description)}""",
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
    try:
        unsent_data = db.get_pending_pesacheck_feeds()
        success_posts = []
        if unsent_data:
            for pending in unsent_data:
                posted = post_to_check_and_update(pending, db=db)
                if posted:
                    success_posts.append(posted)

        from_pesacheck = fetch_from_pesacheck()
        if from_pesacheck:
            for _, item in enumerate(from_pesacheck):
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
                success_posts.append(posted)
        sentry_sdk.capture_message(success_posts)
    except Exception as e:
        sentry_sdk.capture_exception(e)


if __name__ == "__main__":
    try:
        db = PesacheckDatabase()
        if not db:
            sentry_sdk.capture_message("Unable to connect to database")
            sys.exit()
        main(db=db)
    except Exception as e:
        print(e)
        sentry_sdk.capture_exception(e)
        sys.exit()
