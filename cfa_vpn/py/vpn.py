from abc import ABC, abstractmethod
from outline_vpn.outline_vpn import OutlineVPN as OutlineVPNManager

class VPN(ABC):
    @abstractmethod
    def generate_vpn_keys(self, emails):
        pass

class OutlineVPN(VPN):
    def __init__(self, api_url):
        self.client = OutlineVPNManager(api_url=api_url)
        
    def generate_vpn_keys(self, emails):

        for email in emails:
            try:
                self.client.create_key(email)
            except Exception as e:
                print(f"Failed to generate vpn key for {email}: {e}")

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

class VPNManager():
    def __init__(self, emails_loader, vpn):
        self.emails_loader = emails_loader
        self._vpn = vpn

    def set_vpn(self, vpn):
        self._vpn = vpn
    
    def generate_vpn_keys(self):
        emails = self.emails_loader.get_emails()
        successful_emails = self._vpn.generate_vpn_keys(emails)
        self.emails_loader.update_emails(successful_emails)
    
    def send_emails(self):
        emails = self.emails_loader.get_emails()
        print(f"Sending emails to {len(emails)} users")


