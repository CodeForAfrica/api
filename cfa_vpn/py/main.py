import argparse
import os

from dotenv import load_dotenv
from emails.loader import LocalEmailsLoader
from emails.sender import SendGridEmailSender
from vpn import OutlineVPN, VPNManager

load_dotenv("cfa_vpn/.env")


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
    parser.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="Extract VPN usage metrics for every key",
    )
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    vpn_type = os.environ.get("CFA_VPN_TYPE", "outline")

    if vpn_type == "outline":
        outline_vpn_api_url = os.environ.get("CFA_OUTLINE_VPN_API_URL")
        vpn = OutlineVPN(api_url=outline_vpn_api_url)
    else:
        raise ValueError(f"Unsupported vpn type: {vpn_type}")

    email_sender_type = os.environ.get("CFA_EMAIL_SENDER", "sendgrid")

    emails_location = os.environ.get("CFA_EMAILS_LOCATION", "local")
    emails_loader = None
    if emails_location == "local":
        emails_json_path = os.environ.get(
            "CFA_EMAILS_JSON_PATH", "cfa_vpn/py/emails/emails.json"
        )
        emails_loader = LocalEmailsLoader(emails_json_path)
    else:
        raise ValueError(f"Unsupported emails location: {emails_location}")

    vpn_manager = VPNManager(emails_loader=emails_loader, vpn=vpn)

    if args.generate:
        vpn_manager.generate_vpn_keys()

    if args.send:
        if email_sender_type == "sendgrid":
            email_sender = SendGridEmailSender(
                api_key=os.environ.get("CFA_SENDGRID_API_KEY"),
                from_email=os.environ.get("CFA_SENDGRID_FROM_EMAIL"),
                subject=os.environ.get("CFA_EMAIL_SUBJECT", "CFA VPN Access Key"),
            )
        else:
            raise ValueError(f"Unsupported email sender: {email_sender_type}")
        vpn_manager.set_email_sender(email_sender)
        vpn_manager.send_emails()

    if args.extract:
        vpn_manager.extract_user_data()
