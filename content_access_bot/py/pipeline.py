
from db import Database


class RobotsDatabasePipeline:
    def __init__(self):
        self.db = Database()

    def process_item(self, item, spider):
        self.db.insert_current_robots(
            item["airtable_id"],
            item["robots_url"],
            item["robots_timestamp"],
            item["robots_content"],
            item["robots_status"]
        )
        return item

class ArchivedURLsDatabasePipeline:
    def __init__(self):
        self.db = Database() 

    def process_item(self, item, spider):
        # Save the archived URL to the DB
        self.db.insert_internet_archive_snapshot_url(
            item["airtable_id"],
            item["url"],
            item["archive_date"]
        )
        return item

class ArchivedRobotsDatabasePipeline:
    def __init__(self):
        self.db = Database()
    
    def process_item(self, item, spider):
        # Save the archived robots to the DB
        print("ArchivedRobotsDatabasePipeline:", item)
        self.db.insert_internet_archive_snapshot_robots(
            item["id"],
            item["archive_robots_url"],
            item["archived_content"],
            item["archived_retrieval_date"]
        )
        return item

    