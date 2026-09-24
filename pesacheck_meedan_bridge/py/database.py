import sqlite3
from dataclasses import dataclass
from sqlite3 import Error

import settings


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
        self.db_file = settings.PESACHECK_DATABASE_NAME
        self.create_table()

    def create_connection(self):
        return sqlite3.connect(self.db_file)

    def create_table(self):
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS pesacheck_feeds
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
                              claim_description_id TEXT)"""
            )
            conn.commit()
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
            cur.execute(
                sql,
                (
                    feed.title,
                    feed.pubDate,
                    feed.author,
                    feed.guid,
                    feed.link,
                    feed.thumbnail,
                    feed.description,
                    feed.status,
                    feed.categories,
                    feed.check_project_media_id,
                    feed.check_full_url,
                    feed.claim_description_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def update_pesacheck_feed(self, guid, new_feed):
        conn = self.create_connection()
        sql = """UPDATE pesacheck_feeds
                SET title = ?, pubDate = ?, author = ?, link = ?, thumbnail = ?,
                description = ?, status = ?, categories = ?,
                check_project_media_id = ?, check_full_url = ?,
                claim_description_id = ? WHERE guid = ?"""
        try:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    new_feed.title,
                    new_feed.pubDate,
                    new_feed.author,
                    new_feed.link,
                    new_feed.thumbnail,
                    new_feed.description,
                    new_feed.status,
                    new_feed.categories,
                    new_feed.check_project_media_id,
                    new_feed.check_full_url,
                    new_feed.claim_description_id,
                    guid,
                ),
            )
            conn.commit()
            if cur.rowcount != 1:
                raise Error(f"No pesacheck_feeds row with guid {guid}")
        finally:
            conn.close()

    def update_pesacheck_feed_status(self, guid, status):
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE pesacheck_feeds SET status = ? WHERE guid = ?", (status, guid)
            )
            conn.commit()
            if cur.rowcount != 1:
                raise Error(f"No pesacheck_feeds row with guid {guid}")
        finally:
            conn.close()

    def feed_exists(self, guid):
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pesacheck_feeds WHERE guid = ?", (guid,))
            return cur.fetchone() is not None
        finally:
            conn.close()

    def get_ghost_pub_dates(self):
        # Legacy Medium rows use the post URL as guid; Ghost rows use the post id.
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT pubDate FROM pesacheck_feeds "
                "WHERE guid NOT LIKE 'http%' AND pubDate != ''"
            )
            return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    def get_pesacheck_feeds_by_status(self, status):
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pesacheck_feeds WHERE status = ?", (status,))
            rows = cur.fetchall()
            feeds = []
            for row in rows:
                feeds.append(PesacheckFeed(*row))
            return feeds
        finally:
            conn.close()
