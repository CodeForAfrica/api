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

    def update_pesacheck_feed(self, guid, new_feed, expected_status=None):
        conn = self.create_connection()
        sql = """UPDATE pesacheck_feeds
                SET title = ?, pubDate = ?, author = ?, link = ?, thumbnail = ?,
                description = ?, status = ?, categories = ?,
                check_project_media_id = ?, check_full_url = ?,
                claim_description_id = ? WHERE guid = ?"""
        params_tail = []
        if expected_status is not None:
            sql += " AND status = ?"
            params_tail.append(expected_status)
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
                    *params_tail,
                ),
            )
            conn.commit()
            if cur.rowcount != 1:
                raise Error(
                    f"No pesacheck_feeds row with guid {guid}"
                    + (f" in status {expected_status}" if expected_status else "")
                )
        finally:
            conn.close()

    def claim_pending_feed(self, guid):
        """Move a row from Pending to Posting, returning whether we won it.

        Two overlapping runs can both read the same Pending row. SQLite
        serializes the conditional update, so only one of them sees rowcount 1
        and calls Check; the loser leaves the row alone.
        """
        conn = self.create_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE pesacheck_feeds SET status = 'Posting' "
                "WHERE guid = ? AND status = 'Pending'",
                (guid,),
            )
            conn.commit()
            return cur.rowcount == 1
        finally:
            conn.close()

    def update_pesacheck_feed_status(self, guid, status, expected_status=None):
        """Set a row's status, optionally only from an expected one.

        Terminal transitions pass expected_status="Posting" so a row another
        run has already finished can't be overwritten.
        """
        conn = self.create_connection()
        sql = "UPDATE pesacheck_feeds SET status = ? WHERE guid = ?"
        params = [status, guid]
        if expected_status is not None:
            sql += " AND status = ?"
            params.append(expected_status)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            if cur.rowcount != 1:
                raise Error(
                    f"No pesacheck_feeds row with guid {guid}"
                    + (f" in status {expected_status}" if expected_status else "")
                )
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
