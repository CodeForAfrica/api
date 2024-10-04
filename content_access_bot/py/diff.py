import logging

from database import Database, MediaHouse
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
ai_crawlers = [
    "Amazonbot",
    "anthropic-ai",
    "AwarioRssBot",
    "AwarioSmartBot",
    "Bard",
    "Bloom",
    "Bytespider",
    "CCBot",
    "ChatGPT",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "cohere-ai"
    "DataForSeoBot",
    "Diffbot",
    "FacebookBot",
    "GPT-4",
    "GPT-Neo",
    "GPTBot",
    "Google-Extended",
    "GoogleOther",
    "HuggingFace-Transformers",
    "LaMDA",
    "Megatron-Turing-NLG",
    "magpie-crawler",
    "Meltwater",
    "NewsNow",
    "news-please",
    "omgili",
    "OmigiliBot",
    "PaLM",
    "peer39_crawler",
    "peer39_crawler/1.0",
    "PerplexityBot"
    "TurnitinBot",
    "Seekr",
    "Scrapy",
    "Wu-Dao-2.0",
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
        crawler for crawler in ai_crawlers if crawler.casefold() in latest_robots['content'].casefold()
    ]

    archive_crawlers = [
        crawler for crawler in ai_crawlers if crawler.casefold() in oldest_archived_robots['content'].casefold()
    ]

    data = {}
    data['crawler'] = ', '.join(found_crawlers)
    data['archive_crawler'] = archive_crawlers
    data['blocks_crawlers'] = True if found_crawlers else False
    data['notes'] = 'Robots.txt has been updated to block AI crawlers' if found_crawlers and not archive_crawlers else None
    data['latest_robots_url'] = latest_robots['url']
    data['latest_robots_date'] = latest_robots['timestamp']
    data['latest_robots_content'] = latest_robots['content']
    data['archived_robots_url'] = oldest_archived_robots['url']
    data['archived_date'] = oldest_archived_robots['archived_date']
    data['archived_robots_content'] = oldest_archived_robots['content']
    return data
