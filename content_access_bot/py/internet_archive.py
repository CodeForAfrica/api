

import logging
import aiohttp


async def fetch_internet_archive_snapshots(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://web.archive.org/cdx/search/cdx?url={url}"
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    lines = text.split("\n")
                    records = [{
                        "url": fields[2],
                        "timestamp": fields[1],
                        "status": fields[4],
                    } for line in lines if (fields := line.split(" ")) and len(fields) == 7]
                    return records
                return None
    except Exception as e:
        logging.error(f"Failed to fetch snapshots for {url}. Error: {e}")
        return None


def find_closest_snapshot(snapshots, date):
    return next((snapshot for snapshot in reversed(snapshots) if snapshot["timestamp"] <= date), None)
