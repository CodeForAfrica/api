import asyncio
import csv
import random
import aiohttp
from airtable import get_organizations, batch_update_organizations
import logging
from robots import fetch_and_save_robots
from diff import diff_robot_files
import time
import datetime


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

processed_media_houses_csv = "csv/processed_media_houses.csv"


async def update_airtable():
    data_update = []
    with open(processed_media_houses_csv, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # TODO: handle block type
            diff_data = diff_robot_files(row)
            if (diff_data):
                update_data = {
                    'id': row['id'],
                    "fields": {
                        'Current robots.txt': row['robots_url'],
                        'Archive Date': datetime.datetime.strptime(row['timestamp'], "%Y%m%d%H%M%S").date().isoformat(),
                        'Archived robots.txt url': row['archived_robots_url'],
                        "Blocks AI Crawlers": diff_data['blocks_crawlers'],
                        "Blocked Crawlers": diff_data['crawler'],
                        "Block Notes": diff_data['notes'] if diff_data['notes'] else "",
                    }
                }
                data_update.append(update_data)

    await batch_update_organizations(data_update)


async def main():
    allowed_countries = ['Kenya', 'Nigeria', 'South Africa']
    organizations = get_organizations(allowed_countries)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for media_house in organizations:
            task = fetch_and_save_robots(session, media_house)
            tasks.append(task)
        await asyncio.gather(*tasks)
        await asyncio.sleep(random.uniform(1, 3))

    await update_airtable()


if __name__ == '__main__':
    try:
        start_time = time.time()
        asyncio.run(main())
        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
