import datetime
import scrapy

from utils import find_closest_snapshot



class RobotsSpider(scrapy.Spider):
    name = 'robots'
    start_urls = []

    def __init__(self, urls=None, *args, **kwargs):
        super(RobotsSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        for airtable_id, url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'airtable_id': airtable_id}, headers=headers)

    def parse(self, response):
        yield {
            "airtable_id":response.meta['airtable_id'],
            "robots_url": response.url,
            "robots_timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "robots_content":response.text,
            "robots_status":response.status
        }
class ArchivedURLsSpider(scrapy.Spider):
    name = 'archived_urls'
    start_urls = []

    def __init__(self, urls=None, target_date=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls
        # target_date should be a string like "20230618000000"
        self.target_date = target_date or (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m%d%H%M%S")

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        for airtable_id, url in self.start_urls:
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}"
            yield scrapy.Request(
                url=cdx_url,
                callback=self.parse_cdx,
                meta={'airtable_id': airtable_id, 'url':url},
                headers=headers
            )

    def parse_cdx(self, response):
        url = response.meta['url']
        airtable_id = response.meta['airtable_id']
        lines = response.text.strip().split("\n")
        snapshots = []
        for line in lines:
            fields = line.split(" ")
            if len(fields) == 7:
                timestamp = fields[1]
                status= fields[4]
                snapshots.append({
                    "url": f"https://web.archive.org/web/{timestamp}if_/{url}",
                    "timestamp": timestamp,
                })
        closest = find_closest_snapshot(snapshots, self.target_date)
        print("Closest Snapshot:", closest)
        if closest:
            yield {
                "airtable_id": airtable_id,
                "url": closest['url'],
                "archive_date": closest["timestamp"]
            }

class ArchivedRobotsSpider(scrapy.Spider):
    name = 'archived_robots'
    start_urls = []

    def __init__(self, urls=None, *args, **kwargs):
        super(ArchivedRobotsSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        for id, url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'id': id}, headers=headers)

    def parse(self, response):
        yield {
            "id": response.meta['id'],
            "archive_robots_url":response.url,
            "archived_content":response.text,
            "archived_retrieval_date":datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        }
