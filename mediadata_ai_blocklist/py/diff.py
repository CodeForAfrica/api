import os
import glob
import logging
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


def diff_robot_files(media_house):
    country: str = media_house['country']
    name: str = media_house['name']
    data = {}
    robots_file = os.path.join(
        'data', country, name, 'robots.txt'
    )
    archive_files = glob.glob(
        os.path.join('data', country, name, 'archive', '**/*-robots.txt'),
    )

    try:
        with open(robots_file, 'r') as f:
            robots_content = f.read()

        found_crawlers = [
            crawler for crawler in ai_crawlers if crawler in robots_content
        ]

        archive_crawlers = []

        if archive_files:
            with open(archive_files[0], 'r') as f:
                archived_content = f.read()

            archive_crawlers = [
                crawler for crawler in ai_crawlers if crawler in archived_content
            ]

        # TODO: Handle block type
        data['crawler'] = ', '.join(found_crawlers)
        data['archive_crawler'] = archive_crawlers
        data['blocks_crawlers'] = True if found_crawlers else False
        data['notes'] = 'Robots.txt has been updated to block AI crawlers' if found_crawlers and not archive_crawlers else None

    except FileNotFoundError:
        logging.error(f"Robots.txt file not found for {name}")
        pass
    except Exception as e:
        logging.error(f"""Error occurred while reading {
                      name} robots.txt file: {e}""")
        pass

    return data
