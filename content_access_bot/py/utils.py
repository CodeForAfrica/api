import re
from urllib.parse import urlparse, urlunparse
import aiohttp


def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    parsed_url = urlparse(url)
    if parsed_url.scheme == '':
        url = 'http://' + url
        parsed_url = urlparse(url)

    url_str = urlunparse(parsed_url).decode(
        'utf-8') if isinstance(urlunparse(parsed_url), bytes) else urlunparse(parsed_url)

    if re.match(regex, url_str) is not None:
        return url_str
    return None


def clean_url(url):
    parsed_url = urlparse(url)
    cleaned_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, "", "", "", ""))
    return cleaned_url.rstrip('/')


def url_redirects(original, final):
    parsed_original = urlparse(original)
    parsed_final = urlparse(final)

    original_netloc_path = parsed_original.netloc.replace(
        'www.', '') + parsed_original.path.rstrip('/')
    final_netloc_path = parsed_final.netloc.replace(
        'www.', '') + parsed_final.path.rstrip('/')

    return original_netloc_path != final_netloc_path


async def check_site_availability(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, allow_redirects=True) as response:
                return {
                    "status_code": response.status,
                    "reachable": True,
                    "redirect": url_redirects(url, str(response.url)),
                    "final_url": str(response.url)
                }
        except Exception:
            return {
                "status_code": None,
                "reachable": False,
                "redirect": False,
                "final_url": None
            }


def get_robots_url(url: str):
    parsed_url = urlparse(url)
    robots_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, "/robots.txt", "", "", ""))
    return robots_url.rstrip('/')
