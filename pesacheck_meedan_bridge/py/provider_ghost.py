from datetime import UTC

import requests
import settings
from provider_base import USER_AGENT, Article

# Tag names PesaCheck publishes under, mapped to the fact-check language.
LANGUAGE_CODES = {
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


def language_from_categories(categories):
    for category in categories:
        code = LANGUAGE_CODES.get(category.lower())
        if code:
            return code
    return ""


class GhostProvider:
    """PesaCheck on Ghost, read through the (public, read-only) Content API."""

    name = "ghost"

    def __init__(self):
        if not settings.PESACHECK_GHOST_CONTENT_API_KEY:
            raise ValueError(
                "PESACHECK_GHOST_CONTENT_API_KEY is required when "
                "PESACHECK_PROVIDER is 'ghost'"
            )

    def fetch(self, since=None, limit=15, max_articles=None):
        # Oldest first when catching up from a checkpoint, newest page when
        # there is no checkpoint. Returns oldest first either way.
        url = f"{settings.PESACHECK_URL.rstrip('/')}/ghost/api/content/posts/"
        params = {
            "key": settings.PESACHECK_GHOST_CONTENT_API_KEY,
            "limit": limit,
            "order": "published_at asc" if since else "published_at desc",
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
            if max_articles is not None and len(posts) >= max_articles:
                return posts[:max_articles]
            pagination = (data.get("meta") or {}).get("pagination") or {}
            page = pagination.get("next") if since else None
        # The no-checkpoint page came newest first.
        return posts if since else list(reversed(posts))

    def parse(self, post):
        # Internal Ghost tags (e.g. #hash-tags) are for site organisation only.
        categories = [
            tag["name"]
            for tag in post.get("tags") or []
            if tag.get("visibility") == "public"
        ]
        authors = [author["name"] for author in post.get("authors") or []]
        return Article(
            guid=post["id"],
            title=post["title"],
            url=post["url"],
            published_at=post.get("published_at") or "",
            # Ghost excerpts are already plain text.
            summary=(post.get("custom_excerpt") or post.get("excerpt") or "").strip(),
            categories=categories,
            language=language_from_categories(categories),
            author=", ".join(authors),
            thumbnail=post.get("feature_image") or "",
        )
