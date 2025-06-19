import re
from urllib.parse import urlparse, urlunparse
import aiohttp
from datetime import datetime, timedelta


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

    url_unparsed = urlunparse(parsed_url)
    if isinstance(url_unparsed, bytes):
        url_str = url_unparsed.decode('utf-8')
    else:
        url_str = url_unparsed

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

def is_within_time_frame(date_str, days, date_format="%Y-%m-%d"):
    """
    Returns True if date_str is within 'days' from today.
    date_str: string date (e.g. '2024-06-19')
    days: int, number of days from today
    date_format: format of date_str (default: '%Y-%m-%d')
    """
    target_date = datetime.strptime(date_str, date_format)
    today = datetime.today()
    delta = today - target_date
    return 0 <= delta.days <= days


def find_closest_snapshot(snapshots, date, date_key="timestamp"):
    """
    Finds the snapshot closest to the given date.
    If there are snapshots before or on the date, returns the latest one before or on the date.
    If all snapshots are after the date, returns the oldest snapshot.
    """
    if not snapshots:
        return None

    snapshots_sorted = sorted(snapshots, key=lambda x: x[date_key])
    before_or_on = [s for s in snapshots_sorted if s[date_key] <= date]
    if before_or_on:
        return before_or_on[-1]
    else:
        return snapshots_sorted[0]

def format_db_date(date_str):
    """
    Converts a date string like '20240619120000' to 'YYYY-MM-DD HH:MM:SS'.
    Returns None if input is None or invalid.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date_str 
