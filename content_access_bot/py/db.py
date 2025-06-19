import os
from environs import Env, env
from sqlite3 import Error, connect
import logging
from dataclasses import dataclass
from typing import Optional

env = Env()
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
env.read_env(dotenv_path)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
@dataclass
class MediaHouse:
    name: str
    country: str
    url: str
    airtable_id: str
    id: Optional[str] = None
    site_status: Optional[str] = None
    site_reachable: Optional[bool] = None
    site_redirect: Optional[bool] = None
    final_url: Optional[str] = None


class Database:
    def __init__(self):
        self.db_file = os.getenv('DB_FILE') or 'media_data'
        self.conn = self.create_connection()
        self.create_table()

    
    def create_connection(self):
        try:
            conn = connect(self.db_file)
            return conn
        except Error as e:
            logging.error(f"Error creating connectin: {e}")
    
    def is_connected(self):
        return self.conn is not None

    def create_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS media_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            url TEXT NOT NULL,
            airtable_id TEXT NOT NULL UNIQUE,
            site_status TEXT,
            site_reachable BOOLEAN,
            site_redirect BOOLEAN,
            final_url TEXT,
            robots_url TEXT,
            robots_timestamp TEXT,
            robots_content TEXT,
            robots_status TEXT
        );
        CREATE TABLE IF NOT EXISTS internet_archive_snapshots(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airtable_id TEXT NOT NULL, 
            url TEXT NOT NULL,
            archive_date TEXT NOT NULL UNIQUE,
            archive_robots_url TEXT,
            archived_content TEXT,
            archived_retrieval_date TEXT, 
            FOREIGN KEY(airtable_id) REFERENCES media_data(airtable_id)
        );
        """
        try:
            if self.conn is not None:
                cursor = self.conn.cursor()
                cursor.executescript(create_table_sql)
                self.conn.commit()
                logging.info("media_data table created or already exists.")
            else:
                logging.error("Database connection is not established. Table creation skipped.")
        except Error as e:
            logging.error(f"Error creating table: {e}")
    
    def insert_media_house(self, media_house:MediaHouse):
        try:
            sql = """
            INSERT INTO media_data(name, country, url, airtable_id)
            VALUES(?, ?, ?, ?)
            """
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute(sql, (media_house.name, media_house.country,
                            media_house.url, media_house.airtable_id))
                self.conn.commit()
                return cur.lastrowid
            else:
               logging.error("Database connection is not established. Table creation skipped.") 
        except Error as e:
            logging.error(f"Error inserting media house: {e}")

    def close_connection(self, cur):
        if cur is not None:
                cur.close()

    def select_media_houses_without_status(self):
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM media_data WHERE site_status IS NULL")
                rows = cur.fetchall()
                column_names = [column[0] for column in cur.description]
                dict_rows = [dict(zip(column_names, row)) for row in rows]
                return dict_rows
        except Error as e:
            logging.error(f"Errror: ${e}")
        finally:
            self.close_connection(cur)

    def update_site_status(self, airtable_id, site_status, site_reachable, site_redirect, final_url):
        cur = None
        try:
            if self.conn is not None:
                sql = """
                UPDATE media_data
                SET site_status = ?, site_reachable = ?, site_redirect = ?, final_url = ?
                WHERE airtable_id = ?
            """
                cur = self.conn.cursor()
                cur.execute(sql, (site_status, site_reachable,
                            site_redirect, final_url, airtable_id))
                self.conn.commit()
        except Error as e:
            print(e)
        finally:
            self.close_connection(cur)

    def get_all_media_houses(self):
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM media_data")
                rows = cur.fetchall()
                column_names = [column[0] for column in cur.description]
                dict_rows = [dict(zip(column_names, row)) for row in rows]
                return dict_rows
        except Error as e:
            logging.error(f"Errror: ${e}")
        finally:
            self.close_connection(cur)

    def insert_current_robots(self, airtable_id, robots_url,robots_timestamp ,robots_content, robots_status ):
        cur = None
        try:
            if self.conn is not None:
                sql = """
                UPDATE media_data
                SET robots_url = ?, robots_timestamp = ?, robots_content = ?, robots_status = ?
                WHERE airtable_id = ?
            """
                cur = self.conn.cursor()
                cur.execute(sql, (robots_url, robots_timestamp,
                            robots_content, robots_status, airtable_id))
                self.conn.commit()
        except Error as e:
            print(e)
        finally:
            self.close_connection(cur)

    def insert_internet_archive_snapshot_url(self,airtable_id,url,archive_date):
        try:
            sql = """
            INSERT INTO internet_archive_snapshots(airtable_id, url, archive_date)
            VALUES(?, ?, ?)
            """
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute(sql, (airtable_id, url,
                            archive_date))
                self.conn.commit()
                return cur.lastrowid
            else:
               logging.error("Database connection is not established. Table creation skipped.") 
        except Error as e:
            logging.error(f"Error inserting media house: {e}")
    
    def get_all_internet_archive_snapshots(self):
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM internet_archive_snapshots")
                rows = cur.fetchall()
                column_names = [column[0] for column in cur.description]
                dict_rows = [dict(zip(column_names, row)) for row in rows]
                return dict_rows
        except Error as e:
            logging.error(f"Errror: ${e}")
        finally:
            self.close_connection(cur)

    
    def insert_internet_archive_snapshot_robots(self, id, archive_robots_url, archived_content, archived_retrieval_date):
        cur = None
        try:
            if self.conn is not None:
                sql = """
                    UPDATE internet_archive_snapshots
                    SET archive_robots_url = ?, archived_content = ?, archived_retrieval_date = ?
                    WHERE id = ?
                """
                cur = self.conn.cursor()
                cur.execute(sql, (archive_robots_url,archived_content, archived_retrieval_date,id))
                self.conn.commit()
        except Error as e:
            logging.error(f"Errror: ${e}")
        finally:
            self.close_connection(cur)

    def get_combided_data(self):
        """
        Returns a list of dicts, each representing a media_data row with a 'snapshots' key
        containing a list of associated internet_archive_snapshots.
        """
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                # Get all media_data rows
                cur.execute("SELECT * FROM media_data")
                media_rows = cur.fetchall()
                media_columns = [column[0] for column in cur.description]
                combined = []
                for media_row in media_rows:
                    media_dict = dict(zip(media_columns, media_row))
                    # Get all snapshots for this airtable_id
                    cur.execute(
                        "SELECT * FROM internet_archive_snapshots WHERE airtable_id = ?",
                        (media_dict["airtable_id"],)
                    )
                    snapshot_rows = cur.fetchall()
                    snapshot_columns = [column[0] for column in cur.description]
                    snapshots = [dict(zip(snapshot_columns, row)) for row in snapshot_rows]
                    media_dict["snapshots"] = snapshots
                    combined.append(media_dict)
                return combined
        except Error as e:
            logging.error(f"Error: {e}")
        finally:
            self.close_connection(cur)
