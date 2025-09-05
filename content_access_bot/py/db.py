import os
from environs import Env, env
from sqlite3 import Error, connect
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

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

@dataclass
class SiteCheck:
    airtable_id: str
    site_status: Optional[str] = None
    site_reachable: Optional[bool] = None
    site_redirect: Optional[bool] = None
    final_url: Optional[str] = None
    robots_url: Optional[str] = None
    robots_timestamp: Optional[str] = None
    robots_content: Optional[str] = None
    robots_status: Optional[str] = None
    check_timestamp: Optional[str] = None

class Database:
    def __init__(self):
        self.db_file = os.getenv('DB_FILE') or 'media_data'
        self.conn = self.create_connection()
        self.create_table()

    def create_connection(self):
        try:
            conn = connect(self.db_file, timeout=30)
            return conn
        except Error as e:
            logging.error(f"Error creating connection: {e}")
    
    def is_connected(self):
        return self.conn is not None

    def create_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS media_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            url TEXT NOT NULL,
            airtable_id TEXT NOT NULL UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS site_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airtable_id TEXT NOT NULL,
            site_status TEXT,
            site_reachable BOOLEAN,
            site_redirect BOOLEAN,
            final_url TEXT,
            robots_url TEXT,
            robots_timestamp TEXT,
            robots_content TEXT,
            robots_status TEXT,
            check_timestamp TEXT NOT NULL,
            FOREIGN KEY(airtable_id) REFERENCES media_data(airtable_id)
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
                logging.info("Database tables created or already exist.")
            else:
                logging.error("Database connection is not established. Table creation skipped.")
        except Error as e:
            logging.error(f"Error creating table: {e}")
    
    def insert_media_house(self, media_house: MediaHouse):
        try:
            sql = """
            INSERT OR IGNORE INTO media_data(name, country, url, airtable_id)
            VALUES(?, ?, ?, ?)
            """
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute(sql, (media_house.name, media_house.country,
                            media_house.url, media_house.airtable_id))
                self.conn.commit()
                return cur.lastrowid
            else:
               logging.error("Database connection is not established.")
        except Error as e:
            logging.error(f"Error inserting media house: {e}")

    def close_connection(self, cur):
        if cur is not None:
                cur.close()

    def select_media_houses_without_status(self):
        """Legacy method - now returns media houses without recent checks"""
        return self.select_media_houses_without_recent_check()

    def select_media_houses_without_recent_check(self, max_age_days=7):
        """Select media houses that haven't been checked recently or never checked"""
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                # Get media houses with no recent site checks
                sql = """
                SELECT md.* FROM media_data md
                LEFT JOIN (
                    SELECT airtable_id, MAX(check_timestamp) as latest_check
                    FROM site_checks 
                    GROUP BY airtable_id
                ) sc ON md.airtable_id = sc.airtable_id
                WHERE sc.latest_check IS NULL 
                   OR datetime(sc.latest_check) < datetime('now', '-{} days')
                """.format(max_age_days)
                cur.execute(sql)
                rows = cur.fetchall()
                column_names = [column[0] for column in cur.description]
                dict_rows = [dict(zip(column_names, row)) for row in rows]
                return dict_rows
        except Error as e:
            logging.error(f"Error: {e}")
        finally:
            self.close_connection(cur)

    def insert_site_check(self, site_check: SiteCheck):
        """Insert a new site check record"""
        cur = None
        try:
            if self.conn is not None:
                sql = """
                INSERT INTO site_checks(
                    airtable_id, site_status, site_reachable, site_redirect, 
                    final_url, robots_url, robots_timestamp, robots_content, 
                    robots_status, check_timestamp
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cur = self.conn.cursor()
                check_time = site_check.check_timestamp or datetime.now().strftime("%Y%m%d%H%M%S")
                cur.execute(sql, (
                    site_check.airtable_id, site_check.site_status, 
                    site_check.site_reachable, site_check.site_redirect,
                    site_check.final_url, site_check.robots_url,
                    site_check.robots_timestamp, site_check.robots_content,
                    site_check.robots_status, check_time
                ))
                self.conn.commit()
                return cur.lastrowid
        except Error as e:
            logging.error(f"Error inserting site check: {e}")
        finally:
            self.close_connection(cur)

    def update_site_status(self, airtable_id, site_status, site_reachable, site_redirect, final_url):
        """Legacy method - now creates a new site check record for status update"""
        site_check = SiteCheck(
            airtable_id=airtable_id,
            site_status=site_status,
            site_reachable=site_reachable,
            site_redirect=site_redirect,
            final_url=final_url
        )
        return self.insert_site_check(site_check)

    def insert_current_robots(self, airtable_id, robots_url, robots_timestamp, robots_content, robots_status):
        """Legacy method - now creates a new site check record for robots update"""
        site_check = SiteCheck(
            airtable_id=airtable_id,
            robots_url=robots_url,
            robots_timestamp=robots_timestamp,
            robots_content=robots_content,
            robots_status=robots_status
        )
        return self.insert_site_check(site_check)

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
            logging.error(f"Error: {e}")
        finally:
            self.close_connection(cur)

    def get_latest_site_checks(self):
        """Get the most recent site check for each media house"""
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                sql = """
                SELECT sc.* FROM site_checks sc
                INNER JOIN (
                    SELECT airtable_id, MAX(check_timestamp) as latest_check
                    FROM site_checks 
                    GROUP BY airtable_id
                ) latest ON sc.airtable_id = latest.airtable_id 
                AND sc.check_timestamp = latest.latest_check
                """
                cur.execute(sql)
                rows = cur.fetchall()
                column_names = [column[0] for column in cur.description]
                dict_rows = [dict(zip(column_names, row)) for row in rows]
                return dict_rows
        except Error as e:
            logging.error(f"Error: {e}")
        finally:
            self.close_connection(cur)

    def insert_internet_archive_snapshot_url(self, airtable_id, url, archive_date):
        try:
            sql = """
            INSERT INTO internet_archive_snapshots(airtable_id, url, archive_date)
            VALUES(?, ?, ?)
            """
            if self.conn is not None:
                cur = self.conn.cursor()
                cur.execute(sql, (airtable_id, url, archive_date))
                self.conn.commit()
                return cur.lastrowid
            else:
               logging.error("Database connection is not established.")
        except Error as e:
            logging.error(f"Error inserting archive snapshot: {e}")
    
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
            logging.error(f"Error: {e}")
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
                cur.execute(sql, (archive_robots_url, archived_content, archived_retrieval_date, id))
                self.conn.commit()
        except Error as e:
            logging.error(f"Error: {e}")
        finally:
            self.close_connection(cur)

    def get_combided_data(self):
        """Legacy method name - calls get_combined_data"""
        return self.get_combined_data()

    def get_combined_data(self):
        """Get media data with latest site checks and archive snapshots"""
        cur = None
        try:
            if self.conn is not None:
                cur = self.conn.cursor()
                # Get media data with latest site check
                sql = """
                SELECT 
                    md.*,
                    sc.site_status, sc.site_reachable, sc.site_redirect, sc.final_url,
                    sc.robots_url, sc.robots_timestamp, sc.robots_content, sc.robots_status,
                    sc.check_timestamp
                FROM media_data md
                LEFT JOIN (
                    SELECT sc1.* FROM site_checks sc1
                    INNER JOIN (
                        SELECT airtable_id, MAX(check_timestamp) as latest_check
                        FROM site_checks 
                        GROUP BY airtable_id
                    ) sc2 ON sc1.airtable_id = sc2.airtable_id 
                    AND sc1.check_timestamp = sc2.latest_check
                ) sc ON md.airtable_id = sc.airtable_id
                """
                cur.execute(sql)
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
