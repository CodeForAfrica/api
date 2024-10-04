from database import Database


class RobotsDatabasePipeline:
    def __init__(self):
        self.db = Database()

    def process_item(self, item, spider):
        self.db.insert_robot(item)
        return item


class ArchivedRobotsDatabasePipeline:
    def __init__(self):
        self.db = Database()

    def process_item(self, item, spider):
        self.db.insert_archived_robot(item)
        return item
