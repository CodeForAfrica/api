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
    media_house_id = media_house['id']
    latest_robots = db.select_latest_robots(media_house_id)

    if not latest_robots:
        return

    oldest_archived_robots = db.oldest_archived_robots(media_house_id)
    if not oldest_archived_robots:
        return
    found_crawlers = [
        crawler for crawler in ai_crawlers if crawler in latest_robots['content']
    ]

    archive_crawlers = [
        crawler for crawler in ai_crawlers if crawler in oldest_archived_robots['content']
    ]

    data = {}
    data['crawler'] = ', '.join(found_crawlers)
    data['archive_crawler'] = archive_crawlers
    data['blocks_crawlers'] = True if found_crawlers else False
    data['notes'] = 'Robots.txt has been updated to block AI crawlers' if found_crawlers and not archive_crawlers else None
    data['latest_robots_url'] = latest_robots['url']
    data['archived_robots_url'] = oldest_archived_robots['url']
    data['archived_date'] = oldest_archived_robots['archived_date']
    return data
