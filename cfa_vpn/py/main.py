import argparse

from emails.loader import LocalEmailsLoader
from emails.sender import SendGridEmailSender
from environs import Env
from vpn import OutlineVPN, VPNManager

env = Env()
env.read_env()


def init_argparse():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]",
        description="VPN Manager for CFA.",
    )
    parser.add_argument(
        "-g", "--generate", action="store_true", help="Generate VPN keys for emails"
    )
    parser.add_argument(
        "-s",
        "--send",
        action="store_true",
        help="Send emails to users after generating VPN keys",
    )
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    vpn_type = env("CFA_VPN_TYPE", "outline")

    if vpn_type == "outline":
        outline_vpn_api_url = env("CFA_OUTLINE_VPN_API_URL")
        vpn = OutlineVPN(api_url=outline_vpn_api_url)
    else:
        raise ValueError(f"Unsupported vpn type: {vpn_type}")

    email_sender = env("CFA_EMAIL_SENDER", "sendgrid")

    emails_location = env("CFA_EMAILS_LOCATION", "local")
    emails_loader = None
    if emails_location == "local":
        emails_json_path = env("CFA_EMAILS_JSON_PATH", "cfa_vpn/py/emails/emails.json")
        emails_loader = LocalEmailsLoader(emails_json_path)
    else:
        raise ValueError(f"Unsupported emails location: {emails_location}")

    vpn_manager = VPNManager(emails_loader=emails_loader, vpn=vpn)

    if args.generate:
        vpn_manager.generate_vpn_keys()

    if args.send:
        if email_sender == "sendgrid":
            email_sender = SendGridEmailSender(
                api_key=env("CFA_SENDGRID_API_KEY"),
                from_email=env("CFA_SENDGRID_FROM_EMAIL"),
                subject=env("CFA_EMAIL_SUBJECT", "CFA VPN Access Key"),
            )
        else:
            raise ValueError(f"Unsupported email sender: {email_sender}")
        vpn_manager.set_email_sender(email_sender)
        vpn_manager.send_emails()
