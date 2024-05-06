import asyncio
import csv
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

processed_media_houses_csv = "csv/processed_media_houses.csv"


async def update_airtable(db: Database):

    all_orgs = db.select_all_media_houses()
    # print(all_orgs)
    data_update = []
    for org in all_orgs:
        # print(org)
        diff_data = diff_robot_files(org, db)
        if (diff_data):
            print("Diff data: ", diff_data)
            update_data = {
                # 'id': org['url'],
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

    print("Data update: ", data_update)
    await batch_upsert_organizations(data_update)
    # data_update = []
    # with open(processed_media_houses_csv, 'r') as file:
    #     reader = csv.DictReader(file)

    #     for row in reader:
    #         # TODO: handle block type
    #         diff_data = diff_robot_files(row)
    #         if (diff_data):
    #             update_data = {
    #                 'id': row['id'],
    #                 "fields": {
    #                     'Current robots.txt': row['robots_url'],
    #                     'Archive Date': datetime.datetime.strptime(row['timestamp'], "%Y%m%d%H%M%S").date().isoformat(),
    #                     'Archived robots.txt url': row['archived_robots_url'],
    #                     "Blocks AI Crawlers": diff_data['blocks_crawlers'],
    #                     "Blocked Crawlers": diff_data['crawler'],
    #                     "Block Notes": diff_data['notes'] if diff_data['notes'] else "",
    #                 }
    #             }
    #             data_update.append(update_data)

    # await batch_update_organizations(data_update)


async def fetch_orgs(db: Database):
    organizations = get_organizations()
    for media_house in organizations:
        media_house_obj = MediaHouse(
            media_house['name'], media_house['country'], media_house['url'], media_house['id'])
        db.insert_media_house(media_house_obj)


async def fetch_robots(db: Database):
    media_houses = db.select_all_media_houses()
    # only first 30 for testing
    media_houses = media_houses[:30]
    async with aiohttp.ClientSession() as session:
        tasks = []
        for media_house in media_houses:
            task = fetch_current_robots(db, session, media_house)
            tasks.append(task)
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))


async def fetch_archived_robots(db: Database):
    media_houses = db.select_all_media_houses()
    # only first 30 for testing
    media_houses = media_houses[:30]
    async with aiohttp.ClientSession() as session:
        tasks = []
        for media_house in media_houses:
            task = fetch_past_robots(db, session, media_house)
            tasks.append(task)
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))


async def main(db: Database):
    # await fetch_orgs(db)
    # await fetch_robots(db)
    # await fetch_archived_robots(db)
    await update_airtable(db)

    # async with aiohttp.ClientSession() as session:
    #     tasks = []
    #     for media_house in organizations:
    #         task = fetch_and_save_robots(session, media_house)
    #         tasks.append(task)
    #     await asyncio.gather(*tasks)
    #     await asyncio.sleep(random.uniform(1, 3))

    # await update_airtable()


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
