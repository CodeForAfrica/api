from abc import ABC, abstractmethod

from emails.templates import get_outline_email_template
from outline_vpn.outline_vpn import OutlineVPN as OutlineVPNManager


class VPN(ABC):
    @abstractmethod
    def generate_vpn_keys(self, emails):
        pass

    @abstractmethod
    def get_vpn_keys(self, emails=None):
        # if emails is None, return all vpn keys
        pass


class OutlineVPN(VPN):
    def __init__(self, api_url):
        self.client = OutlineVPNManager(api_url=api_url)

    # generate vpn keys for emails and return a list of emails we generated keys for
    def generate_vpn_keys(self, emails):
        success_emails = []
        for email in emails:
            try:
                self.client.create_key(email)
                success_emails.append(email)
            except Exception as e:
                print(f"Failed to generate VPN key for {email}: {e}")
        return success_emails

    def get_vpn_keys(self, emails):
        all_keys = self.client.get_keys()
        if emails is None:
            return all_keys
        else:
            return [key for key in all_keys if key.name in emails]


class VPNManager:
    def __init__(self, emails_loader, vpn):
        self.emails_loader = emails_loader
        self._vpn = vpn
        self._email_sender = None

    def set_vpn(self, vpn):
        self._vpn = vpn

    def set_email_sender(self, email_sender):
        self._email_sender = email_sender

    def generate_vpn_keys(self):
        emails = self.emails_loader.get_emails_without_vpn()
        successful_emails = self._vpn.generate_vpn_keys(emails)
        self.emails_loader.update_vpn_keys_access_status(successful_emails)

    def send_emails(self):
        emails = self.emails_loader.get_emails_to_send()
        # Depending on the VPN type, we may need to have different email templates
        if isinstance(self._vpn, OutlineVPN):
            keys = self._vpn.get_vpn_keys(emails)
            success_emails = []
            for key in keys:
                self._email_sender.set_body(get_outline_email_template(key))
                if self._email_sender.send(key.name):
                    success_emails.append(key.name)
            self.emails_loader.update_email_sent_status(success_emails)
        else:
            # For now, we only support Outline VPN
            raise ValueError(f"Unsupported VPN type: {type(self._vpn)}")
