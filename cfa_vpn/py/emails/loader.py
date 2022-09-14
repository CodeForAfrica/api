import json
from abc import ABC, abstractmethod


class EmailsLoader(ABC):
    @abstractmethod
    def get_emails_without_vpn(self):
        pass

    # get emails that have vpn access and haven't been sent yet
    def get_emails_to_send(self):
        pass

    @abstractmethod
    def update_vpn_users_state(self, emails, status):
        pass


class LocalEmailsLoader(EmailsLoader):
    def __init__(self, path):
        self.path = path

    def _load(self):
        with open(self.path, "r") as f:
            return f.read()

    def get_emails_without_vpn(self):
        emails = json.loads(self._load()).get("emails", [])
        # return only emails without vpn keys
        return [email["name"] for email in emails if not email.get("has_vpn_access")]

    # get emails that have vpn access and haven't been sent yet
    def get_emails_to_send(self):
        emails = json.loads(self._load()).get("emails", [])
        return [
            email["name"]
            for email in emails
            if email.get("has_vpn_access") and not email.get("sent")
        ]

    def update_vpn_users_state(self, emails, state, value):
        emails_json = json.loads(self._load())
        for email in emails_json["emails"]:
            if email["name"] in emails:
                email[state] = value
        with open(self.path, "w") as f:
            f.write(json.dumps(emails_json))


class GsheetEmailsLoader(EmailsLoader):
    pass
