import asyncio
import random
import aiohttp
from airtable import get_organizations, batch_upsert_organizations
import logging
from robots import fetch_current_robots, fetch_past_robots
from diff import diff_robot_files
import time
import datetime
from database import Database, MediaHouse


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def update_airtable(db: Database):
    all_orgs = db.select_all_media_houses()
    data_update = []
    for org in all_orgs:
        diff_data = diff_robot_files(org, db)
        if (diff_data):
            update_data = {
                "fields": {
                    "URL": org['url'],
                    "Organisation Name": org['name'],
                    "Blocks AI Crawlers": diff_data['blocks_crawlers'],
                    "Blocked Crawlers": diff_data['crawler'],
                    "Current Robots": diff_data['latest_robots_url'],
                    "Archived Robots": diff_data['archived_robots_url'],
                    "Archive Date": datetime.datetime.strptime(diff_data['archived_date'], "%Y%m%d%H%M%S").date().isoformat(),
                }
            }
            data_update.append(update_data)

    await batch_upsert_organizations(data_update)


async def fetch_orgs(db: Database):
    organizations = get_organizations()
    for media_house in organizations:
        media_house_obj = MediaHouse(
            media_house['name'], media_house['country'], media_house['url'], media_house['id'])
        db.insert_media_house(media_house_obj)


async def fetch_robots(db: Database):
    media_houses = db.select_all_media_houses()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_current_robots(
            db, session, media_house)) for media_house in media_houses]
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))


async def fetch_archived_robots(db: Database):
    media_houses = db.select_all_media_houses()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_past_robots(
            db, session, media_house)) for media_house in media_houses]
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))


async def main(db: Database):
    await fetch_orgs(db)
    await asyncio.gather(fetch_robots(db), fetch_archived_robots(db))
    await update_airtable(db)


if __name__ == '__main__':
    try:
        start_time = time.time()
        db = Database()
        if not db.is_connected():
            logging.error("Failed to connect to the database")
            exit(1)
        asyncio.run(main(db))
        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
