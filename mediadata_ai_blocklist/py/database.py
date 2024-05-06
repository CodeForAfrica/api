import sqlite3
from dataclasses import dataclass
from sqlite3 import Error
from typing import List
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')


@dataclass
class MediaHouse:
    name: str
    country: str
    url: str
    airtable_id: str
    id: str = None


@dataclass
class Robots:
    media_house_id: str
    url: str
    timestamp: str
    content: str
    status: str


@dataclass()
class ArchivedRobots:
    media_house_id: str
    url: str
    archived_date: str
    content: str
    timestamp: str
    status: str


class Database:
    def __init__(self):
        load_dotenv(dotenv_path)
        self.db_file = os.getenv('DB_FILE')
        self.conn = self.create_connection()
        self.create_table()

    def create_connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(e)

    def create_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS media_house (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            airtable_id TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS robots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_house_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(media_house_id) REFERENCES media_house(id)
        );
        CREATE TABLE IF NOT EXISTS archived_robots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_house_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            archived_date TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(media_house_id) REFERENCES media_house(id)
        );
        """
        try:
            c = self.conn.cursor()
            c.executescript(create_table_sql)
        except Error as e:
            print(e)
        finally:
            c.close()

    def insert_media_house(self, media_house: MediaHouse):
        try:
            sql = """
            INSERT INTO media_house(name, country, url, airtable_id)
            VALUES(?, ?, ?, ?)
            """
            cur = self.conn.cursor()
            cur.execute(sql, (media_house.name, media_house.country,
                        media_house.url, media_house.airtable_id))
            self.conn.commit()
            return cur.lastrowid
        except Error as e:
            print(e)
        finally:
            cur.close()

    def select_all_media_houses(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM media_house")
            rows = cur.fetchall()
            column_names = [column[0] for column in cur.description]
            dict_rows = [dict(zip(column_names, row)) for row in rows]
            return dict_rows
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()

    def select_media_house_by_id(self, id):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM media_house WHERE id=?", (id,))
            row = cur.fetchone()
            return row
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()

    def select_media_house_by_name(self, name):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM media_house WHERE name=?", (name,))
            row = cur.fetchone()
            return row
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()

    def update_media_house(self, media_house: MediaHouse):
        sql = """
        UPDATE media_house
        SET name = ?,
            country = ?,
            url = ?
        WHERE id = ?
        """
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (media_house.name, media_house.country,
                        media_house.url, media_house.id))
            self.conn.commit()
        except Error as e:
            print(e)
        finally:
            cur.close()

    def delete_media_house(self, id):
        try:
            sql = "DELETE FROM media_house WHERE id=?"
            cur = self.conn.cursor()
            cur.execute(sql, (id,))
            self.conn.commit()
        except Error as e:
            print(e)
        finally:
            cur.close()

    def close_connection(self):
        self.conn.close()

    def is_connected(self):
        return self.conn is not None

    def insert_robot(self, robot: Robots):
        try:
            sql = """
            INSERT INTO robots(media_house_id, url, timestamp, content, status)
            VALUES(?, ?, ?, ?, ?)
            """
            cur = self.conn.cursor()
            cur.execute(sql, (robot.media_house_id, robot.url,
                        robot.timestamp, robot.content, robot.status))
            self.conn.commit()
            return cur.lastrowid
        except Error as e:
            print(e)
        finally:
            cur.close()

    def insert_archived_robot(self, archived_robot: ArchivedRobots):
        try:
            sql = """
            INSERT INTO archived_robots(media_house_id, url, archived_date, content, timestamp, status)
            VALUES(?, ?, ?, ?, ?, ?)
            """
            cur = self.conn.cursor()
            cur.execute(sql, (archived_robot.media_house_id, archived_robot.url,
                        archived_robot.archived_date, archived_robot.content, archived_robot.timestamp, archived_robot.status))
            self.conn.commit()
            return cur.lastrowid
        except Error as e:
            print(e)
        finally:
            cur.close()

    def select_latest_robots(self, media_house_id):
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM robots WHERE media_house_id=? ORDER BY timestamp DESC LIMIT 1", (media_house_id,))
            row = cur.fetchone()
            if row is None:
                return None
            dict_row = dict(zip([column[0] for column in cur.description], row))
            return dict_row
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()

    def select_latest_archived_robots(self, media_house_id):
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM archived_robots WHERE media_house_id=? ORDER BY timestamp DESC LIMIT 1", (media_house_id,))
            row = cur.fetchone()
            if row is None:
                return None
            dict_row = dict(zip([column[0] for column in cur.description], row))
            return dict_row
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()

    def oldest_archived_robots(self, media_house_id):
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM archived_robots WHERE media_house_id=? ORDER BY timestamp ASC LIMIT 1", (media_house_id,))
            row = cur.fetchone()
            if row is None:
                return None
            dict_row = dict(zip([column[0] for column in cur.description], row))
            return dict_row
        except Error as e:
            print(e)
            return None
        finally:
            cur.close()
