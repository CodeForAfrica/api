import json
from pyairtable import Api
from dotenv import load_dotenv
from utils import validate_url, clean_url
import os
import logging
import re


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
organisations_table = os.getenv('AIRTABLE_ORGANISATION_TABLE')

if not api_key or not base_id or not organisations_table:
    raise ValueError('API key, base ID and Organisation table are required')

at = Api(api_key)


def get_table_data(table_name, formula=None, fields=None):
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

# TODO: Implement better caching mechanism


def get_organizations(allowed_countries=None, cache=True):
    if cache:
        try:
            with open('cache/organizations.json', 'r') as f:
                logging.info('Fetching organizations from cache')
                return json.loads(f.read())
        except FileNotFoundError:
            logging.info('Cache file not found. Fetching from Airtable')
            pass

    formula = get_formula(allowed_countries)
    fields = ['Organisation Name', 'Website', 'HQ Country']
    data = get_table_data('Organisation', formula, fields)
    organizations = process_records(data)
    if cache:
        os.makedirs('cache', exist_ok=True)
        with open('cache/organizations.json', 'w') as f:
            f.write(json.dumps(organizations))

    return organizations


async def batch_update_organizations(data):
    logging.info('Updating organizations in Airtable')
    try:
        table = at.table(base_id, 'Organisation')
        table.batch_update(records=data)
    except Exception as e:
        logging.error(f'Error updating organization: {e}')
