import sqlite3
from sqlite3 import Error
from dataclasses import dataclass
import os
import settings
import sentry_sdk


@dataclass
class PesacheckFeed:
    title: str
    pubDate: str
    author: str
    guid: str
    link: str
    thumbnail: str
    description: str
    status: str
    categories: str
    check_project_media_id: str = ""
    check_full_url: str = ""
    claim_description_id: str = ""


class PesacheckDatabase:
    def __init__(self):
        path = os.path.dirname(os.path.realpath(__file__))
        db_file = os.path.join(path, settings.PESACHECK_DATABASE_NAME)
        self.db_file = db_file
        self.create_table()

    def create_connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            sentry_sdk.capture_exception(e)
        return None

    def create_table(self):
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS pesacheck_feeds
                              (title TEXT NOT NULL,
                              pubDate TEXT NOT NULL,
                              author TEXT NOT NULL,
                              guid TEXT PRIMARY KEY,
                              link TEXT NOT NULL,
                              thumbnail TEXT NOT NULL,
                              description TEXT NOT NULL,
                              status TEXT DEFAULT 'Pending',
                              categories TEXT DEFAULT '[]',
                              check_project_media_id TEXT,
                              check_full_url TEXT,
                              claim_description_id TEXT)''')
            conn.commit()
        except Error as e:
            sentry_sdk.capture_exception(e)
        finally:
            conn.close()

    def insert_pesacheck_feed(self, feed):
        conn = self.create_connection()
        sql = """INSERT INTO pesacheck_feeds (title, pubDate, author,
                 guid, link, thumbnail, description, status, categories,
                 check_project_media_id, check_full_url, claim_description_id)
                 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (feed.title, feed.pubDate, feed.author, feed.guid,
                              feed.link, feed.thumbnail,
                              feed.description, feed.status, feed.categories,
                              feed.check_project_media_id, feed.check_full_url,
                              feed.claim_description_id))
            conn.commit()
        except Error as e:
            sentry_sdk.capture_exception(e)
        finally:
            conn.close()

    def update_pesacheck_feed(self, guid, new_feed):
        conn = self.create_connection()
        sql = '''UPDATE pesacheck_feeds
                SET title = ?, pubDate = ?, author = ?, link = ?, thumbnail = ?,
                description = ?, status = ?, categories = ?,
                check_project_media_id = ?, check_full_url = ?,
                claim_description_id = ? WHERE guid = ?'''
        try:
            cur = conn.cursor()
            cur.execute(sql, (new_feed.title, new_feed.pubDate, new_feed.author,
                              new_feed.link, new_feed.thumbnail,
                              new_feed.description, new_feed.status,
                              new_feed.categories, new_feed.check_project_media_id,
                              new_feed.check_full_url,
                              new_feed.claim_description_id,
                              guid
                              ))
            conn.commit()
        except Error as e:
            sentry_sdk.capture_exception(e)
        finally:
            conn.close()

    def get_pending_pesacheck_feeds(self):
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pesacheck_feeds WHERE status = 'Pending'")
            rows = cur.fetchall()
            feeds = []
            for row in rows:
                feeds.append(PesacheckFeed(*row))
            return feeds
        except Error as e:
            sentry_sdk.capture_exception(e)
        finally:
            conn.close()
