import re

import requests
from check_api_queries import create_mutation_query
import settings
import sentry_sdk


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
    raise Exception(response.status_code, message="An Error Occurred fetching data from pesacheck")


def post_to_check(query):
    headers = {
        "Content-Type": "application/json",
        "X-Check-Token": settings.PESACHECK_CHECK_TOKEN,
        "X-Check-Team": settings.PESACHECK_CHECK_WORKSPACE_SLUG,
    }
    body = dict(query=query)
    url = settings.PESACHECK_CHECK_URL
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code == 200:
        return response.json()
    raise Exception(response.status_code, message=response.text)


def upload_content():
    try:
        items = fetch_from_pesacheck()
        if items:
            success_posts = []
            for _, item in enumerate(items):
                language = "fr" if "french" in item.get("categories") else "en"
                input_data = {
                    "media_type": "Blank",
                    "channel": 1,
                    "set_tags": item["categories"],
                    "set_status": "verified",
                    "set_claim_description": remove_html_tags(item["description"]),
                    "title": remove_html_tags(item["title"]),
                    "summary": remove_html_tags(item["description"]),
                    "url": item["link"],
                    "language": language,
                    "publish_report": True,
                }
                query = create_mutation_query(**input_data)
                res = post_to_check(query)
                if res:
                    success_posts.append(res)
            sentry_sdk.capture_message("Successful Uploads", success_posts)
    except Exception as e:
        sentry_sdk.capture_exception(e)


if __name__ == "__main__":
    upload_content()
