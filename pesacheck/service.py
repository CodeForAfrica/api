import re
import requests
import os
from dotenv import load_dotenv
from mutation_queries import create_mutation_query, delete_mutation_query
from sentry_sdk import init, capture_exception, capture_message, set_context

load_dotenv()


init(
    dsn=os.getenv("PESACHECK_SENTRY_DSN"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


def log_error(code, message=""):
    capture_message(f"Status code: {code}\n Error: {message}")


def remove_html_tags(input_string):
    return re.sub(r'<[^>]*>', '', input_string)


def fetch_from_pesacheck():
    url = "https://api.rss2json.com/v1/api.json"
    rss_api_key = os.getenv("PESACHECK_RSS_2_JSON_API_KEY")
    feed_url = os.getenv("PESACHECK_URL")
    params = {'rss_url': feed_url, 'api_key': rss_api_key, 'count': 10, 'order_by': 'pubDate'}
    response = requests.get(url, params=params, timeout=60)
    if response.status_code == 200:
        return response.json().get('items') or []
    log_error(code=response.status_code, message=response.text)
    return []


def post_to_check(query):
    try:
        headers = {"Content-Type": "application/json",
                   "X-Check-Token": os.getenv("PESACHECK_TOKEN"), "X-Check-Team": os.getenv("PESACHECK_WORKSPACE_SLUG")}
        body = dict(query=query)
        url = os.getenv("PESACHECK_CHECK_URL")
        response = requests.post(url, headers=headers, json=body, timeout=60)
        if response.status_code == 200:
            return response.json()
        log_error(code=response.status_code, message=response.text)
        return None
    except Exception as e:
        capture_exception(e)


def upload_content():
    items = fetch_from_pesacheck()
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
        if (res):
            success_posts.append(res)
    set_context("Successful Uploads", success_posts)
