import json
from datetime import UTC

import requests
import settings
from provider_base import USER_AGENT, Article, html_to_text

# An article is a fact-check iff it carries a verdict from the "Debunk"
# vocabulary. Without this clause the query also returns homepage blocks, team
# profiles and Media Centre entries, which publish to the same routes.
DEBUNK_SCHEME = "Debunk"

# Subject vocabularies that become Check tags: language, country, the kind of
# fact-check, and the harm it addresses. Order is the tag order.
CATEGORY_SCHEMES = ["Debunklang", "countries", "content_type", "Harm_type"]

FACT_CHECKS_QUERY = """
  query FactChecks($where: swp_article_bool_exp!, $limit: Int!, $offset: Int!) {
    items: swp_article(
      where: $where
      order_by: { published_at: desc }
      limit: $limit
      offset: $offset
    ) {
      id
      title
      slug
      lead
      published_at
      metadata
      swp_route {
        slug
      }
    }
  }
"""


def parse_metadata(raw):
    # Hasura exposes the jsonb `metadata` column as a JSON-encoded string.
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def subject_names(metadata, scheme):
    return [
        subject["name"]
        for subject in metadata.get("subject") or []
        if subject.get("scheme") == scheme and subject.get("name")
    ]


class SuperdeskProvider:
    """PesaCheck on Superdesk, read through Publisher's GraphQL API."""

    name = "superdesk"

    def __init__(self):
        if not settings.PESACHECK_SUPERDESK_GRAPHQL_URL:
            raise ValueError(
                "PESACHECK_SUPERDESK_GRAPHQL_URL is required when "
                "PESACHECK_PROVIDER is 'superdesk'"
            )
        if not settings.PESACHECK_SUPERDESK_TENANT_CODE:
            raise ValueError(
                "PESACHECK_SUPERDESK_TENANT_CODE is required when "
                "PESACHECK_PROVIDER is 'superdesk'"
            )

    def build_where(self, since=None):
        published_at = {"_is_null": False}
        if since:
            # published_at is stored without an offset; the API treats it as UTC.
            published_at["_gte"] = since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        return {
            "tenant_code": {"_eq": settings.PESACHECK_SUPERDESK_TENANT_CODE},
            "published_at": published_at,
            "_and": [
                {
                    "swp_article_metadata": {
                        "swp_article_metadata_subjects": {
                            "scheme": {"_eq": DEBUNK_SCHEME}
                        }
                    }
                }
            ],
        }

    def fetch(self, since=None, limit=15):
        # Without a checkpoint (first run against Superdesk), only fetch the
        # newest page instead of backfilling PesaCheck's entire archive.
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
        if settings.PESACHECK_SUPERDESK_PRESHARED_AUTH:
            # A Cloudflare WAF rule skips bot protection when this matches.
            headers["x-preshared-auth"] = settings.PESACHECK_SUPERDESK_PRESHARED_AUTH
        where = self.build_where(since)
        articles = []
        offset = 0
        while True:
            body = {
                "query": FACT_CHECKS_QUERY,
                "variables": {"where": where, "limit": limit, "offset": offset},
            }
            response = requests.post(
                settings.PESACHECK_SUPERDESK_GRAPHQL_URL,
                json=body,
                headers=headers,
                timeout=60,
            )
            if response.status_code != 200:
                raise Exception(
                    f"An Error Occurred fetching data from pesacheck: {response.text}"
                )
            data = response.json()
            if data.get("errors"):
                raise Exception(
                    f"An Error Occurred fetching data from pesacheck: {response.text}"
                )
            page = ((data.get("data") or {}).get("items")) or []
            articles.extend(page)
            if not since or len(page) < limit:
                break
            offset += limit
        return articles

    def parse(self, article):
        metadata = parse_metadata(article.get("metadata"))
        categories = []
        for scheme in CATEGORY_SCHEMES:
            categories.extend(subject_names(metadata, scheme))
        published_at = article.get("published_at") or ""
        if published_at and not published_at.endswith("Z") and "+" not in published_at:
            # Naive in the API, UTC in fact; store it unambiguously.
            published_at = f"{published_at}+00:00"
        return Article(
            # The Superdesk guid survives a re-import; the numeric id may not.
            guid=str(metadata.get("guid") or article["id"]),
            title=article["title"],
            url=self.article_url(article),
            published_at=published_at,
            summary=html_to_text(article.get("lead")),
            categories=categories,
            language=metadata.get("language") or "",
            author=metadata.get("byline") or "",
            # Check never receives a thumbnail, so the renditions aren't worth
            # resolving here.
            thumbnail="",
        )

    def article_url(self, article):
        base = settings.PESACHECK_SITE_URL.rstrip("/")
        desk = (article.get("swp_route") or {}).get("slug")
        slug = article["slug"]
        return f"{base}/fact-checks/{desk}/{slug}" if desk else f"{base}/{slug}"
