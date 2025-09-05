from datetime import datetime, timedelta
import logging
import time
import logging
import asyncio
from airtable import get_organizations, batch_upsert_organizations
from scrapy.crawler import CrawlerProcess
import pandas as pd
from db import Database, MediaHouse, SiteCheck
from diff import diff_robot_content
from spider import ArchivedRobotsSpider, ArchivedURLsSpider, RobotsSpider
from utils import check_site_availability, get_robots_url,find_closest_snapshot,format_db_date


MAX_ROBOTS_AGE = 7 # No of Days to skip fetching of current robots
MAX_INTERNATE_ARCHIVE_AGE =365

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_orgs(db:Database):
    organizations = get_organizations()
    for media_house in organizations:
        media_house_obj = MediaHouse(
            media_house['name'], media_house['country'], media_house['url'], media_house['id']
        )
        db.insert_media_house(media_house_obj)


async def check_org_sites(db:Database):
    unchecked_orgs = db.select_media_houses_without_recent_check()
    if not unchecked_orgs:
        logging.info(f"No sites to check")
        return
    count = len(unchecked_orgs) if unchecked_orgs is not None else 0
    logging.info(f"Checking {count} sites")

    async def update_org_site(org):
        site_status = await check_site_availability(org['url'])
        db.update_site_status(
            org['airtable_id'], site_status['status_code'],
            site_status['reachable'], site_status['redirect'], site_status['final_url']
        )
    #TODO:Use Spider to check sites
    await asyncio.gather(*(update_org_site(org) for org in unchecked_orgs))
    logging.info("Finished checking Sites")


async def fetch_robots(db: Database):
    all_media_houses = db.get_all_media_houses()
    if not all_media_houses:
        logging.info(f"No sites to check")
        return

    # Get latest site checks to determine which need robot fetching
    latest_checks = db.get_latest_site_checks()
    check_dict = {check['airtable_id']: check for check in latest_checks}
    
    filtered_media_houses = []
    today = datetime.now()
    
    for media_house in all_media_houses:
        airtable_id = media_house['airtable_id']
        latest_check = check_dict.get(airtable_id)
        
        if not latest_check or not latest_check.get('robots_content'):
            filtered_media_houses.append(media_house)
            continue
            
        robots_timestamp = latest_check.get('robots_timestamp')
        if robots_timestamp:
            try:
                robots_date = datetime.strptime(robots_timestamp, "%Y%m%d%H%M%S")
                if (today - robots_date).days > MAX_ROBOTS_AGE:
                    filtered_media_houses.append(media_house)
            except Exception as e:
                logging.warning(f"Invalid robots_timestamp for {airtable_id}: {robots_timestamp}")

    count = len(filtered_media_houses)
    if count == 0:
        logging.info("No robots to fetch within the specified timeframe.")
        return

    logging.info(f"Fetching Robots for {count} sites")
    urls = [(media_house['airtable_id'], get_robots_url(media_house['url']))
            for media_house in filtered_media_houses]
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            'pipeline.RobotsDatabasePipeline': 1
        },
    }, install_root_handler=False)
    process.crawl(RobotsSpider, urls)
    process.start()

async def fetch_internet_archive_snapshots(db: Database):
    logging.info("fetch_internet_archive_snapshots")
    all_media_houses = db.get_all_media_houses()
    if not all_media_houses:
        logging.info(f"No sites to fetch internet archive snapshots")
        return

    all_archive_snapshots = db.get_all_internet_archive_snapshots()
    # Get set of airtable_ids that already have snapshots
    fetched_airtable_ids = set(s['airtable_id'] for s in all_archive_snapshots) if all_archive_snapshots else set()
    # Filter only media houses not yet fetched
    to_fetch = [media_house for media_house in all_media_houses if media_house['airtable_id'] not in fetched_airtable_ids]

    count = len(to_fetch)
    if count == 0:
        logging.info("No new sites to fetch internet archive snapshots for.")
        return

    logging.info(f"Fetching Internet Archive snapshots for {count} sites")
    target_date = (datetime.now() - timedelta(days=MAX_INTERNATE_ARCHIVE_AGE)).strftime("%Y%m%d%H%M%S")
    urls = [(media_house['airtable_id'], media_house['url']) for media_house in to_fetch]
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            'pipeline.ArchivedURLsDatabasePipeline': 2
        },
    }, install_root_handler=False)
    process.crawl(ArchivedURLsSpider, urls=urls, target_date=target_date)
    process.start()

async def fetch_archived_robots(db:Database):
    logging.info("Fetching Archived Robots.tx")
    all_archived_snapshot_url = db.get_all_internet_archive_snapshots()
    if not all_archived_snapshot_url:
        logging.info(f"No sites to fetch internet archive snapshots")
        return

    today = datetime.now()
    filtered_snapshots = []
    for snapshot in all_archived_snapshot_url:
        archived_content = snapshot.get('archived_content')
        archived_retrieval_date = snapshot.get('archived_retrieval_date')
        # If archived_content is None or empty, always include
        if not archived_content:
            filtered_snapshots.append(snapshot)
            continue
        # If archived_retrieval_date exists, check if it's older than MAX_ROBOTS_AGE days
        if archived_retrieval_date:
            try:
                retrieval_date = datetime.strptime(archived_retrieval_date, "%Y%m%d%H%M%S")
                if (today - retrieval_date).days > MAX_ROBOTS_AGE:
                    filtered_snapshots.append(snapshot)
            except Exception as e:
                logging.warning(f"Invalid archived_retrieval_date for {snapshot.get('id')}: {archived_retrieval_date}")

    count = len(filtered_snapshots)
    if count == 0:
        logging.info("No archived robots to fetch within the specified timeframe.")
        return

    logging.info(f"Fetching Robots for {count} sites")
    urls = [(snapshot['id'], f"{snapshot['url']}/robots.txt")
                for snapshot in filtered_snapshots]
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            'pipeline.ArchivedRobotsDatabasePipeline': 3
        },
    }, install_root_handler=False) 
    process.crawl(ArchivedRobotsSpider, urls)
    process.start()


async def generate_report(db: Database):
    combined_data = db.get_combined_data()
    if not combined_data:
        logging.info("No Data to generate report from")
        return
    target_date = (datetime.now() - timedelta(days=MAX_INTERNATE_ARCHIVE_AGE)).strftime("%Y%m%d%H%M%S")
    report_rows = []

    for media in combined_data:
        snapshots = media.get("snapshots", [])
        closest_snapshot = find_closest_snapshot(snapshots, target_date,date_key="archive_date")
        archived_content = ""
        row = {
            "Name": media.get("name"),
            "Country": media.get("country"),
            "URL": media.get("url"),
            "Airtable ID": media.get("airtable_id"),
            "Site Status": media.get("site_status"),
            "Site Reachable": bool(media.get("site_reachable")),
            "Site Redirect": bool(media.get("site_redirect")),
            "Final URL": media.get("final_url"),
            "Robots URL": media.get("robots_url"),
            "Date Robots Fetched": format_db_date(media.get("robots_timestamp")),
            "Robot Content": (
                "''" if media.get("robots_content") == "" else media.get("robots_content")
            ),
            "Robot Status": media.get("robots_status"),
        }
        if closest_snapshot:
            row.update({
                "Archive URL": closest_snapshot.get("url"),
                "Archive Date": format_db_date(closest_snapshot.get("archive_date")),
                "Archive Robots URL": closest_snapshot.get("archive_robots_url"),
                "Archive Robot Content": (
                    "''" if closest_snapshot.get("archive_robots_url") == "" else closest_snapshot.get("archive_robots_url")
                ),
                "Archive Retrievel Date": format_db_date(closest_snapshot.get("archived_retrieval_date")),
            })
            archived_content = closest_snapshot.get("archived_content") 
        else:
            row.update({
                "Archive URL": None,
                "Archive Date": None,
                "Archive Robots URL": None,
                "Archive Robot Content": None,
                "Archive Retrievel Date": None,
            })
        report_rows.append(row)

        diff_data = diff_robot_content(media.get("robots_content"),archived_content)

        row.update(({
            "Blocks AI Crawlers": diff_data['blocks_crawlers'],
            "Blocked AI Crawler": diff_data['blocked_crawlers'],
            "Update Robots to block AI":diff_data['ai_blocking_update']
        }))
        

    df = pd.DataFrame(report_rows)
    filename = f"Report-{target_date}.xlsx"
    df.to_excel(filename, index=False)

async def main(db:Database):
    await fetch_orgs(db)
    await check_org_sites(db) # Often Not Required unless site status is required
    await fetch_robots(db)
    await fetch_internet_archive_snapshots(db)
    await fetch_archived_robots(db)
    await generate_report(db)


if __name__ == "__main__":
    try:
        start_time = time.time()
        db = Database()
        if not db.is_connected():
            logging.error("Failed to connect to the database")
            exit(1)
        asyncio.run(main(db))
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    
