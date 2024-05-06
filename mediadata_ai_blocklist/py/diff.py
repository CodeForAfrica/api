import os
import glob
import logging

from database import Database, MediaHouse
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
ai_crawlers = [
    "GPTBot",
    "ChatGPT-User",
    "anthropic-ai",
    "Google-Extended",
    "CCBot",
    "FacebookBot",
    "Amazonbot",
    "Claude-Web",
    "cohere-ai",
    "Bard",
    "ChatGPT",
    "GPT-4",
    "HuggingFace-Transformers",
    "LaMDA",
    "Megatron-Turing-NLG",
    "Wu-Dao-2.0",
    "PaLM",
    "GPT-Neo",
    "Bloom"
]


def diff_robot_files(media_house: MediaHouse, db: Database):
    # print("DIFF Media house: ", media_house)
    media_house_id = media_house['id']
    latest_robots = db.select_latest_robots(media_house_id)

    if not latest_robots:
        return

    oldest_archived_robots = db.oldest_archived_robots(media_house_id)
    if not oldest_archived_robots:
        return

    # print("Oldest archived robots: ", oldest_archived_robots)
    # print("Latest robots: ", latest_robots)

    found_crawlers = [
        crawler for crawler in ai_crawlers if crawler in latest_robots['content']
    ]
    # print("Found crawlers: ", found_crawlers)

    archive_crawlers = [
        crawler for crawler in ai_crawlers if crawler in oldest_archived_robots['content']
    ]
    # print("Archive crawlers: ", archive_crawlers)

    data = {}
    data['crawler'] = ', '.join(found_crawlers)
    data['archive_crawler'] = archive_crawlers
    data['blocks_crawlers'] = True if found_crawlers else False
    data['notes'] = 'Robots.txt has been updated to block AI crawlers' if found_crawlers and not archive_crawlers else None
    data['latest_robots_url'] = latest_robots['url']
    data['archived_robots_url'] = oldest_archived_robots['url']
    data['archived_date'] = oldest_archived_robots['archived_date']
    # data['url'] = media_house['url']
    return data

    # country: str = media_house['country']
    # name: str = media_house['name']
    # data = {}
    # robots_file = os.path.join(
    #     'data', country, name, 'robots.txt'
    # )
    # archive_files = glob.glob(
    #     os.path.join('data', country, name, 'archive', '**/*-robots.txt'),
    # )

    # try:
    #     with open(robots_file, 'r') as f:
    #         robots_content = f.read()

    #     found_crawlers = [
    #         crawler for crawler in ai_crawlers if crawler in robots_content
    #     ]

    #     archive_crawlers = []

    #     if archive_files:
    #         with open(archive_files[0], 'r') as f:
    #             archived_content = f.read()

    #         archive_crawlers = [
    #             crawler for crawler in ai_crawlers if crawler in archived_content
    #         ]

    #     # TODO: Handle block type
    #     data['crawler'] = ', '.join(found_crawlers)
    #     data['archive_crawler'] = archive_crawlers
    #     data['blocks_crawlers'] = True if found_crawlers else False
    #     data['notes'] = 'Robots.txt has been updated to block AI crawlers' if found_crawlers and not archive_crawlers else None

    # except FileNotFoundError:
    #     logging.error(f"Robots.txt file not found for {name}")
    #     pass
    # except Exception as e:
    #     logging.error(f"""Error occurred while reading {
    #                   name} robots.txt file: {e}""")
    #     pass

    # return data
