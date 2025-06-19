from pyairtable import Api
from utils import validate_url, clean_url
import os
import logging
import re
from environs import Env
env = Env()
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')

env.read_env(dotenv_path)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
organisations_table = os.getenv('AIRTABLE_ORGANISATION_TABLE')
content_table = os.getenv('AIRTABLE_CONTENT_TABLE')

if not api_key or not base_id or not organisations_table or not content_table:
    raise ValueError('API key, base ID and Organisation table are required')

at = Api(api_key)


def get_table_data(table_name, formula=None, fields=None):
    if not base_id:
        logging.error(f"AIRTABLE_BASE_ID Not Provided")
        return
    table = at.table(base_id, table_name)
    return table.all(formula=formula, fields=fields)


def get_formula(allowed_countries=None):
    base_formula = 'AND(NOT({Organisation Name} = ""), NOT({Website} = ""), NOT({HQ Country} = ""))'
    if allowed_countries:
        countries_formula = ', '.join(
            [f'({{HQ Country}} = "{country}")' for country in allowed_countries])
        formula = f'AND({base_formula}, OR({countries_formula}))'
    else:
        formula = base_formula
    return formula


def process_records(data):
    organizations = []
    for record in data:
        website = validate_url(record['fields'].get('Website', None))
        name = record['fields'].get('Organisation Name', None)
        country = record['fields'].get('HQ Country', None)
        id: str = record['id']
        if website:
            org = {}
            org['id'] = id
            org['name'] = re.sub(
                r'[\\/*?:"<>|]', '-', name) if name else None
            org['url'] = clean_url(website)
            org['country'] = country

            organizations.append(org)
    return organizations


def get_organizations(allowed_countries=None):
    logging.info('Fetching organizations from Airtable')
    formula = get_formula(allowed_countries)
    fields = ['Organisation Name', 'Website', 'HQ Country']
    data = get_table_data(organisations_table, formula, fields)
    organizations = process_records(data)
    logging.info(f'Fetched {len(organizations)} organizations')
    return organizations


async def batch_upsert_organizations(data):
    logging.info('Upserting organizations in Airtable')
    try:
        if not base_id or not content_table:
            logging.error(f"AIRTABLE_BASE_ID or AIRTABLE_CONTENT_TABLE Not Provided")
            return
        table = at.table(base_id, content_table)
        table.batch_upsert(records=data, key_fields=['id',])
        logging.info('Organizations upserted successfully')
    except Exception as e:
        logging.error(f'Error upserting organization: {e}')
