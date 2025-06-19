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


def diff_robot_content(current_robots_content: str, archived_robots_content: str):
    """
    Compares two robots.txt contents.
    Returns:
        - blocks_crawlers: True if current robots.txt blocks any AI crawlers
        - blocked_crawlers: List of AI crawlers blocked in current robots.txt
        - ai_blocking_update: True if current robots.txt blocks AI crawlers but archived did not
    """
    current_content = current_robots_content or ""
    archived_content = archived_robots_content or ""

    blocked_crawlers = [
        crawler for crawler in ai_crawlers if crawler.casefold() in current_content.casefold()
    ]
    previously_blocked_crawlers = [
        crawler for crawler in ai_crawlers if crawler.casefold() in archived_content.casefold()
    ]

    blocks_crawlers = bool(blocked_crawlers)
    ai_blocking_update = blocks_crawlers and not previously_blocked_crawlers

    return {
        "blocks_crawlers": blocks_crawlers,
        "blocked_crawlers": ', '.join(blocked_crawlers),
        "ai_blocking_update": ai_blocking_update,
    }
