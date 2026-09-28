from dataclasses import dataclass, field

import lxml.html  # nosec B410

# Identify the bridge instead of defaulting to "python-requests/x.y.z", which
# Cloudflare challenges in front of pesacheck.org. Kept separate from
# py/VERSION, which isn't packaged into the pex.
USER_AGENT = "PesaCheckMeedanBridge/1.0 (+https://pesacheck.org)"


@dataclass
class Article:
    """A fact-check as the bridge sees it, whichever CMS it came from."""

    guid: str
    title: str
    url: str
    published_at: str
    # Plain text: each provider strips its own markup.
    summary: str = ""
    categories: list = field(default_factory=list)
    # ISO code ("en", "so", ...); empty when the provider can't tell.
    language: str = ""
    author: str = ""
    thumbnail: str = ""


def html_to_text(value):
    """Collapse an HTML fragment to plain text. Safe on plain text and None."""
    if not value or not value.strip():
        return ""
    return lxml.html.fromstring(value).text_content().strip()
