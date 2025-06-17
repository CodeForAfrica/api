from sqliteDB import Database


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
        id = item.media_house_id
        timestamp = item.timestamp
        status = item.status
        content = item.content

        self.db.update_archived_robot_content(
            archived_robot_id=id,
            content=content,
            status=status,
            timestamp=timestamp,
        )
        return item
