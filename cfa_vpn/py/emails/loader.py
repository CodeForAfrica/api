from abc import ABC, abstractmethod
import json


class EmailsLoader(ABC):
    @abstractmethod
    def get_emails(self):
        pass
    
    @abstractmethod
    def update_emails(self, emails):
        pass

class LocalEmailsLoader(EmailsLoader):
    def __init__(self, path=None):
        self.path = path or "cfa_vpn/py/emails/emails.json"

    def _load(self):
        with open(self.path, 'r') as f:
            return f.read()
    
    def get_emails(self):
        emails = json.loads(self._load()).get('emails', [])
        # return only emails without vpn keys
        return [email['name'] for email in emails if not email.get('has_vpn_access')]

    def update_emails(self, emails):
        emails_json = json.loads(self._load())
        for email in emails_json['emails']:
            if email['name'] in emails:
                email['has_vpn_access'] = True
        with open(self.path, 'w') as f:
            f.write(json.dumps(emails_json))

class GsheetEmailsLoader(EmailsLoader):
    pass
