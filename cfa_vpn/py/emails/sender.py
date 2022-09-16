from abc import ABC, abstractmethod
from dataclasses import dataclass

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


@dataclass
class EmailSender(ABC):
    from_email: str
    subject: str
    _body: str = None

    @abstractmethod
    def set_body(self, body):
        pass

    @abstractmethod
    def send(self, to_email):
        pass


@dataclass
class SendGridEmailSender(EmailSender):
    api_key: str = None

    def set_body(self, body):
        self._body = body

    def send(self, to_email):
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=self.subject,
            html_content=self._body,
        )
        try:
            sg = SendGridAPIClient(self.api_key)
            # Fix this:
            import ssl

            ssl._create_default_https_context = ssl._create_unverified_context

            response = sg.send(message)
            if response.status_code == 202:
                return True
        except Exception as e:
            print(e.message)
        return False
