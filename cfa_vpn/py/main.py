import argparse

from vpn import VPNManager, OutlineVPN
from emails.loader import LocalEmailsLoader

from environs import Env

env = Env()
env.read_env()

def init_argparse():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]",
        description="VPN Manager for CFA.",
    )
    parser.add_argument("-g", "--generate", action="store_true", help="Generate VPN keys for emails")
    parser.add_argument("-s", "--send", action="store_true", help="Send emails to users after generating VPN keys")
    return parser

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()

    vpn = None
    vpn_type = env('VPN_TYPE', 'outline')

    emails_location = env('EMAILS_LOCATION', 'local')
    emails_loader = None
    if emails_location == 'local':
        emails_loader = LocalEmailsLoader()
    else:
        raise ValueError(f"Unsupported emails location: {emails_location}")

    vpn_manager = VPNManager(emails_loader=emails_loader, vpn=vpn)

    if args.generate:
        if vpn_type == 'outline':
            outline_vpn_api_url = env('OUTLINE_VPN_API_URL')
            vpn = OutlineVPN(api_url=outline_vpn_api_url)
            vpn_manager.set_vpn(vpn)
        else:
            raise ValueError(f"Unsupported vpn type: {vpn_type}")
        vpn_manager.generate_vpn_keys()
    
    if args.send:
        vpn_manager.send_emails()
