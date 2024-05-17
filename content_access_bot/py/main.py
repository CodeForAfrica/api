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
from utils import check_site_availability


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def update_airtable(db: Database):
    all_orgs = db.get_reachable_sites()
    logging.info(f"Updating {len(all_orgs)} sites")
    data_update = []
    for org in all_orgs:
        diff_data = diff_robot_files(org, db)
        if (diff_data):
            update_data = {
                "fields": {
                    "id": org['airtable_id'],
                    "Blocks AI Crawlers": diff_data['blocks_crawlers'],
                    "Blocked Crawlers": diff_data['crawler'],
                    "Current Robots URL": diff_data['latest_robots_url'],
                    "Checked": datetime.datetime.strptime(diff_data['latest_robots_date'], "%Y%m%d%H%M%S").date().isoformat(),
                    "Current Robots Content": diff_data['latest_robots_content'],
                    "Archived Robots URL": diff_data['archived_robots_url'],
                    "Archive Date": datetime.datetime.strptime(diff_data['archived_date'], "%Y%m%d%H%M%S").date().isoformat(),
                    "Archived Robots Content": diff_data['archived_robots_content'],
                }
            }
            data_update.append(update_data)

    await batch_upsert_organizations(data_update)
    logging.info("Finished updating sites")


async def update_airtable_site_status(db: Database):
    all_orgs = db.select_all_media_houses()
    logging.info(f"Updating {len(all_orgs)} sites status")
    data_update = []
    for org in all_orgs:
        update_data = {
            "fields": {
                "id": org['airtable_id'],
                "Organisation": [org['airtable_id']],
                "URL": org['url'],
                "Reachable": bool(org['site_reachable']),
                "Redirects": bool(org['site_redirect']),
                "Final URL": org['final_url'],
            }
        }
        data_update.append(update_data)

    await batch_upsert_organizations(data_update)
    logging.info("Finished updating sites status")


async def fetch_orgs(db: Database):
    organizations = get_organizations()
    for media_house in organizations:
        media_house_obj = MediaHouse(
            media_house['name'], media_house['country'], media_house['url'], media_house['id'])
        db.insert_media_house(media_house_obj)


async def fetch_robots(db: Database):
    media_houses = db.get_reachable_sites()
    logging.info(f"Fetching robots for {len(media_houses)} sites")
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_current_robots(
            db, session, media_house)) for media_house in media_houses]
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))
    logging.info("Finished fetching robots")


async def fetch_archived_robots(db: Database):
    media_houses = db.get_reachable_sites()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_past_robots(
            db, session, media_house)) for media_house in media_houses]
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))


async def check_org_sites(db: Database):
    all_orgs = db.select_all_media_houses()
    logging.info(f"Checking {len(all_orgs)} sites")

    async def update_org_site(org):
        site_status = await check_site_availability(org['url'])
        db.update_site_status(org['id'], site_status['status_code'],
                              site_status['reachable'], site_status['redirect'], site_status['final_url'])

    await asyncio.gather(*(update_org_site(org) for org in all_orgs))
    logging.info("Finished checking sites")


async def main(db: Database):
    await fetch_orgs(db)
    await check_org_sites(db)
    await update_airtable_site_status(db)
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
