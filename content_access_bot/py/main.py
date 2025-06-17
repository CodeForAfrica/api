import asyncio
import random
import aiohttp
from airtable import get_organizations, batch_upsert_organizations
import logging
from robots import fetch_past_robots, should_fetch_past_robots
from diff import diff_robot_files
import time
from datetime import datetime, timedelta
from sqliteDB import Database, MediaHouse
from utils import check_site_availability, get_robots_url
from spider import RobotsSpider, ArchivedRobotsSpider
from scrapy.crawler import CrawlerProcess
from internet_archive import fetch_internet_archive_snapshots, find_closest_snapshot


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
                    "Checked": datetime.strptime(diff_data['latest_robots_date'], "%Y%m%d%H%M%S").date().isoformat(),
                    "Current Robots Content": diff_data['latest_robots_content'],
                    "Archived Robots URL": diff_data['archived_robots_url'],
                    "Archive Date": datetime.strptime(diff_data['archived_date'], "%Y%m%d%H%M%S").date().isoformat(),
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
                "Organisation": org['name'],
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
    media_houses = db.get_reachable_sites_without_robots()
    logging.info(f"Fetching robots for {len(media_houses)} sites")
    urls = [(media_house['id'], get_robots_url(media_house['url']))
            for media_house in media_houses]
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            'pipeline.RobotsDatabasePipeline': 1
        },
    }, install_root_handler=False)
    process.crawl(RobotsSpider, urls)
    process.start()


async def get_internet_archive_urls(db:Database):
    media_houses = db.get_reachable_sites_without_archived_robots_urls()
    logging.info(f"Fetching archived robots for {len(media_houses)} sites")
    past_days = 365
    one_year_ago = (datetime.now() - timedelta(days=past_days)
                    ).strftime("%Y%m%d%H%M%S")
    for media_house in media_houses:
        if await should_fetch_past_robots(db, media_house):
            archived_robots = await fetch_internet_archive_snapshots(
                media_house['url'])
            if archived_robots:
                closest_snapshot = find_closest_snapshot(
                    archived_robots, one_year_ago)
                if closest_snapshot:
                    print("Closest snapshot::", closest_snapshot)
                    # TODO: (@kelvinkipruto) Internet Archive now renders content in an iframe, so we need to adjust the URL accordingly. A quick fix is to add "if_/" before the URL path.
                    # closest_snapshot_url = f"https://web.archive.org/web/{closest_snapshot['timestamp']}/{media_house['url']}"
                    closest_snapshot_url = f"https://web.archive.org/web/{closest_snapshot['timestamp']}if_/{media_house['url']}"

                    db.insert_archived_robots_urls(media_house['id'], closest_snapshot_url, closest_snapshot['timestamp'])
                    logging.info(
                        f"Found archived robots for {media_house['name']}: {closest_snapshot_url}")
                    await asyncio.sleep(random.uniform(1, 3))
                else:
                    logging.info(
                        f"No archived robots found for {media_house['name']}")
        else:
            logging.info(f"Skipping {media_house['name']}")


async def fetch_archived_robots(db: Database):
    media_houses = db.get_archived_robots_without_content()
    print(f"Fetching archived robots for {len(media_houses)} sites")
    urls = [(media_house['id'], media_house['url'], media_house['archived_date'])
            for media_house in media_houses]
    archived_robots_urls = [(id, f"{url}/robots.txt", timestamp) for id,
                           url, timestamp in urls]
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            'pipeline.ArchivedRobotsDatabasePipeline': 1
        },
    }, install_root_handler=False)
    process.crawl(ArchivedRobotsSpider, archived_robots_urls)
    process.start()


async def check_org_sites(db: Database):
    all_orgs = db.select_media_houses_without_status()
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
    await fetch_robots(db)
    await get_internet_archive_urls(db)
    # await asyncio.gather(fetch_robots(db), get_internet_archive_urls(db))
    await fetch_archived_robots(db)
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
