import json
import re

import requests
import sentry_sdk
import settings
from check_api import create_mutation_query
from database import PesacheckDatabase, PesacheckFeed


def remove_html_tags(input_string):
    return re.sub(r"<[^>]*>", "", input_string)


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
    raise Exception(
        response.status_code, message="An Error Occurred fetching data from pesacheck"
    )


def post_to_check(query):
    headers = {
        "Content-Type": "application/json",
        "X-Check-Token": settings.PESACHECK_CHECK_TOKEN,
        "X-Check-Team": settings.PESACHECK_CHECK_WORKSPACE_SLUG,
    }
    body = dict(query=query)
    url = settings.PESACHECK_CHECK_URL
    return {
        "data": {
            "createProjectMedia": {
                "project_media": {
                    "id": "UHJvamVjdE1lZGlhLzI2MzcyNDY=",
                    "full_url": "project/16148/media/2637246",
                    "claim_description": {
                        "fact_check": {"id": "RmFjdENoZWNrLzgyNzIyMg=="}
                    },
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code == 200:
        return response.json()
    raise Exception(response.status_code, message=response.text)


def store_in_database(feed):
    db = PesacheckDatabase()
    db.insert_pesacheck_feed(feed)
    return feed


def post_to_check_and_update(feed):
    categories = json.loads(feed.categories)
    language = "fr" if "french" in categories else "en"
    input_data = {
        "media_type": "Blank",
        "channel": 1,
        "set_tags": categories,
        "set_status": "verified",
        "set_claim_description": remove_html_tags(feed.description),
        "title": remove_html_tags(feed.title),
        "summary": remove_html_tags(feed.description),
        "url": feed.link,
        "language": language,
        "publish_report": True,
    }
    query = create_mutation_query(**input_data)
    res = post_to_check(query)
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
        feed.status = 'Completed'
        db = PesacheckDatabase()
        db.update_pesacheck_feed(feed.guid, feed)
        return feed


def main():
    try:
        db = PesacheckDatabase()
        unsent_data = db.get_pending_pesacheck_feeds()
        success_posts = []
        if unsent_data:
            for pending in unsent_data:
                posted = post_to_check_and_update(pending)
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
                    claim_description_id=""
                )
                store_in_database(feed)
                post_to_check_and_update(feed)
        sentry_sdk.capture_message("Successful Uploads", success_posts)
    except Exception as e:
        sentry_sdk.capture_exception(e)


if __name__ == "__main__":
    main()
