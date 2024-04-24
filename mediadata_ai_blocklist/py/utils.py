import re
from urllib.parse import urlparse, urlunparse


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
