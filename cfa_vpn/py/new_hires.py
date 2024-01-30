import gspread
from google.oauth2.service_account import Credentials
from outline_vpn.outline_vpn import OutlineVPN
from environs import Env
from emails.templates import get_outline_email_template
from emails.sender import SendGridEmailSender


env = Env()
env.read_env()

def process_new_hires(sheet_id, sheet_name, vpn_api_url):
    credentials_file = env("CFA_GOOGLE_CREDENTIALS_PATH")
    credentials = Credentials.from_service_account_file(credentials_file, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    g_sheet = gspread.authorize(credentials)
    sheet = g_sheet.open_by_key(sheet_id)
    worksheet = sheet.worksheet(sheet_name)
    values = worksheet.get_all_values()
    vpn_manager = OutlineVPN(api_url=vpn_api_url)
    email_sender_type = env("CFA_EMAIL_SENDER", "sendgrid")
    titles = values[0]
    for i, row in enumerate(values, start=1):
        email_address_created = row[titles.index('Email Address Created')]
        email_address = row[titles.index('Email Address')]
        outline_key_created = row[titles.index('Outline Key Created?')]
        outline_key = row[titles.index('Outline Key')]
        
        if email_address and outline_key_created != "Yes" and not outline_key:
            key = vpn_manager.create_key(email_address)
            worksheet.update_cell(i, titles.index('Outline Key Created?') + 1, "Yes")
            worksheet.update_cell(i, titles.index('Outline Key') + 1, key.access_url)
            if email_sender_type == "sendgrid":
                email_sender = SendGridEmailSender(api_key=env("CFA_SENDGRID_API_KEY"),from_email=env("CFA_SENDGRID_FROM_EMAIL"),subject=env("CFA_EMAIL_SUBJECT", "CFA VPN Access Key"),)
                email_sender.set_body(get_outline_email_template(key))
                email_sender.send(key.name)
                worksheet.update_cell(i, titles.index('Key sent') + 1, "Yes")
            else:
                raise ValueError(f"Unsupported email sender: {email_sender_type}")
                
sheet_id = env("CFA_NEW_HIRES_SHEET_ID")
sheet_name = env("CFA_NEW_HIRES_SHEET_NAME")
vpn_api_url = env("CFA_OUTLINE_VPN_API_URL")
process_new_hires(sheet_id=sheet_id, sheet_name=sheet_name, vpn_api_url=vpn_api_url)