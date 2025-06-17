import datetime
import scrapy
from sqliteDB import Robots, ArchivedRobots


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

        for id, url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'id': id}, headers=headers)

    def parse(self, response):
        item = Robots(
            media_house_id=response.meta['id'],
            url=response.url,
            content=response.text,
            timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            status=response.status
        )
        yield item


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

        for id, url, archived_date in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'id': id, 'archived_date': archived_date}, headers=headers)

    def parse(self, response):
        item = ArchivedRobots(
            media_house_id=response.meta['id'],
            url=response.url,
            content=response.text,
            archived_date=response.meta['archived_date'],
            timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            status=response.status
        )
        yield item
