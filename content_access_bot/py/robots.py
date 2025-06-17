import asyncio
import re
import aiohttp
from datetime import datetime, timedelta
import logging
import backoff
import random

from sqliteDB import Database, MediaHouse, Robots, ArchivedRobots


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


retries = 1
timeout = 240
past_days = 365
semaphore = asyncio.Semaphore(10)


def is_valid_robots_txt(text):
    text = re.sub(r'(#.*)?\n', '', text)

    if not re.search(r'^\s*(User-agent|Disallow)\s*:', text, re.MULTILINE | re.IGNORECASE):
        return False

    if not re.match(r'^\s*(User-agent|Disallow|Allow|Crawl-delay|Sitemap)\s*:', text, re.IGNORECASE):
        return False

    return True


@backoff.on_exception(backoff.expo,
                      (aiohttp.ClientError, aiohttp.ClientResponseError),
                      max_tries=retries,
                      giveup=lambda e: e.status not in [429, 500, 502, 503, 504, 522])
async def fetch_with_backoff(session, url, headers, retry_count=0):
    try:
        response = await session.get(url, headers=headers)
        if response.status == 429:  # Rate limit error code
            if retry_count < 3:
                retry_after = int(response.headers.get("Retry-After", "15"))
                logging.warning(f"""RATE LIMITED:: for {url}. Retrying after {
                                retry_after} seconds. Attempt {retry_count + 1}""")
                await asyncio.sleep(retry_after)
                return await fetch_with_backoff(session, url, headers, retry_count + 1)
            else:
                logging.error(f"""Failed to fetch {
                              url} after 3 attempts due to rate limit.""")
                return None
        else:
            return await response.text()

    except Exception as e:
        logging.error(f"Failed to fetch {url}. Error: {e}")
        return None


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404)
async def fetch_robots(session, url):
    async with semaphore:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        if url.endswith('/'):
            robots_url = f"{url}robots.txt"
        else:
            robots_url = f"{url}/robots.txt"
        logging.info(f"Fetching robots.txt for {robots_url}")

        try:
            text = await fetch_with_backoff(session, robots_url, headers)
            if text:
                await asyncio.sleep(random.uniform(1, 3))
                if (not is_valid_robots_txt(text)):
                    logging.error(
                        f"Invalid robots.txt for {robots_url}. Skipping")
                    return None
                return text
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logging.error(f"robots.txt not found at {robots_url}")
                return None
            else:
                logging.error(f"""Failed to fetch robots.txt for {
                              robots_url}. Error: {e}""")
            return None
        except Exception as e:
            logging.error(f"""ClientResponseError:: Failed to fetch robots.txt for {
                          robots_url}. Error: {e}""")
            return None

        logging.error(
            f"Exception:: Failed to fetch robots.txt for {robots_url}")
        return None


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404)
async def fetch_current_robots(db: Database, session: aiohttp.ClientSession, media_house: MediaHouse):
    latest_robots = db.select_latest_robots(media_house['id'])
    if latest_robots:
        last_fetch = datetime.strptime(
            latest_robots['timestamp'], "%Y%m%d%H%M%S")
        if (datetime.now() - last_fetch) < timedelta(days=1):
            logging.info(
                f"Skipping robots.txt fetch for {media_house['name']}")
            return

    url = media_house['url']
    if url.endswith('/'):
        robots_url = f"{url}robots.txt"
    else:
        robots_url = f"{url}/robots.txt"

    try:
        text = await fetch_robots(session, url)
        if text:
            robots = Robots(media_house['id'], robots_url,
                            datetime.now().strftime("%Y%m%d%H%M%S"), text, "200")
            db.insert_robot(robots)
            await asyncio.sleep(random.uniform(1, 3))
    except Exception as e:
        logging.error(f"""ClientResponseError:: Failed to fetch robots.txt for {
                      robots_url}. Error: {e}""")

    logging.error(
        f"Exception:: Failed to fetch robots.txt for {robots_url}")
    return None


async def should_fetch_past_robots(db: Database, media_house: MediaHouse):
    latest_archived_robots = db.select_latest_archived_robots(media_house['id'])
    if latest_archived_robots:
        last_fetch = datetime.strptime(
            latest_archived_robots['timestamp'], "%Y%m%d%H%M%S")
        if (datetime.now() - last_fetch) < timedelta(days=1):
            logging.info(
                f"Skipping past robots.txt fetch for {media_house['name']}")
            return False
    return True


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404)
async def fetch_past_robots(db: Database, session: aiohttp.ClientSession, media_house: MediaHouse):
    latest_archived_robots = db.select_latest_archived_robots(media_house['id'])
    if latest_archived_robots:
        last_fetch = datetime.strptime(
            latest_archived_robots['timestamp'], "%Y%m%d%H%M%S")
        if (datetime.now() - last_fetch) < timedelta(days=1):
            logging.info(
                f"Skipping past robots.txt fetch for {media_house['name']}")
            return
    snapshots = await fetch_internet_archive_snapshots(session, media_house['url'])
    if snapshots:
        one_year_ago = (datetime.now() - timedelta(days=past_days)
                        ).strftime("%Y%m%d%H%M%S")
        closest_snapshot = find_closest_snapshot(snapshots, one_year_ago)
        logging.info(f"""Closest snapshot for {
            media_house['name']}: {closest_snapshot}""")
        if closest_snapshot:
            closest_snapshot_url = f"https://web.archive.org/web/{closest_snapshot['timestamp']}/{media_house['url']}"
            logging.info(f"""Closet snapshot URL for {
                media_house['name']}: {closest_snapshot_url}""")
            archive_robots = await fetch_robots(session, closest_snapshot_url)
            if archive_robots:
                archive_robots = ArchivedRobots(media_house['id'], closest_snapshot_url,
                                                closest_snapshot['timestamp'], archive_robots, datetime.now().strftime("%Y%m%d%H%M%S"), "200")
                db.insert_archived_robot(archive_robots)
                await asyncio.sleep(random.uniform(1, 3))
        else:
            logging.error(
                f"No snapshot found for {media_house['name']} in the past year")


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: e.status == 404)
async def fetch_internet_archive_snapshots(session, url):
    async with semaphore:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        archive_url = f"https://web.archive.org/cdx/search/cdx?url={url}"
        logging.info(f"Fetching internet archive snapshots for {url}")

        text = await fetch_with_backoff(session, archive_url, headers)
        if text:
            lines = text.split("\n")
            records = [{
                "url": fields[2],
                "timestamp": fields[1],
                "status": fields[4],
            } for line in lines if (fields := line.split(" ")) and len(fields) == 7]
            await asyncio.sleep(random.uniform(1, 3))
            return records

        logging.error(
            f"Failed to fetch internet archive snapshots for {archive_url}")
        return None


def find_closest_snapshot(snapshots, date):
    return next((snapshot for snapshot in reversed(snapshots) if snapshot["timestamp"] <= date), None)
