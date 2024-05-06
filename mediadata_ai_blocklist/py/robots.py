import os
import asyncio
import re
import aiohttp
from datetime import datetime, timedelta
import logging
import backoff
import random
import csv

from database import Database, MediaHouse, Robots, ArchivedRobots


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

processed_media_houses_csv = "csv/processed_media_houses.csv"


retries = 1
timeout = 240
past_days = 365
semaphore = asyncio.Semaphore(10)


def should_fetch_robots(media_house):
    with open(processed_media_houses_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['id'] == media_house['id']:
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
                return text
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logging.error(f"robots.txt not found at {robots_url}")
                return None
            else:
                logging.error(f"""Failed to fetch robots.txt for {
                              robots_url}. Error: {e}""")
            raise
        except Exception as e:
            logging.error(f"""ClientResponseError:: Failed to fetch robots.txt for {
                          robots_url}. Error: {e}""")

        logging.error(
            f"Exception:: Failed to fetch robots.txt for {robots_url}")
        return None


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404)
async def fetch_current_robots(db: Database, session: aiohttp.ClientSession, media_house: MediaHouse):
    async with semaphore:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        # print(media_house)
        url = media_house['url']
        if url.endswith('/'):
            robots_url = f"{url}robots.txt"
        else:
            robots_url = f"{url}/robots.txt"
        logging.info(f"Fetching robots.txt for {robots_url}")

        try:
            text = await fetch_with_backoff(session, robots_url, headers)
            if text:
                print("Valid robots.txt")
                robots = Robots(media_house['id'], robots_url,
                                datetime.now().strftime("%Y%m%d%H%M%S"), text, "200")
                print(robots)
                db.insert_robot(robots)
                await asyncio.sleep(random.uniform(1, 3))
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logging.error(f"robots.txt not found at {robots_url}")
                return None
            else:
                logging.error(f"""Failed to fetch robots.txt for {
                              robots_url}. Error: {e}""")
            raise
        except Exception as e:
            logging.error(f"""ClientResponseError:: Failed to fetch robots.txt for {
                          robots_url}. Error: {e}""")

        logging.error(
            f"Exception:: Failed to fetch robots.txt for {robots_url}")
        return None


@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=retries,
                      giveup=lambda e: isinstance(e, aiohttp.ClientResponseError) and e.status == 404)
async def fetch_past_robots(db: Database, session: aiohttp.ClientSession, media_house: MediaHouse):
    snapshots = await fetch_internet_archive_snapshots(session, media_house['url'])
    if snapshots:
        print("Snapshots")
        one_year_ago = (datetime.now() - timedelta(days=past_days)
                        ).strftime("%Y%m%d%H%M%S")
        closest_snapshot = find_closest_snapshot(snapshots, one_year_ago)
        logging.info(f"""Closest snapshot for {
            media_house['name']}: {closest_snapshot}""")
        if closest_snapshot:
            closest_snapshot_url = f"https://web.archive.org/web/{
                closest_snapshot['timestamp']}/{media_house['url']}"
            logging.info(f"""Closet snapshot URL for {
                media_house['name']}: {closest_snapshot_url}""")
            archive_robots = await fetch_robots(session, closest_snapshot_url)
            if archive_robots:
                print("Valid robots.txt")
                archive_robots = ArchivedRobots(media_house['id'], closest_snapshot_url,
                                                closest_snapshot['timestamp'], archive_robots, datetime.now().strftime("%Y%m%d%H%M%S"), "200")
                print(archive_robots)
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
