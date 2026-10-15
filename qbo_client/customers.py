from qbo_client.client import query
from qbo_client.auth import get_access_token
from qbo_client.custom_fields import get_custom_field, CUSTOM_FIELDS_QUERY_PARAMS
import logging
import os

# ids are sent in the query string, so batches are kept small enough for a short URL.
# QBO also returns only 100 rows by default, so MAXRESULTS is set to match
CUSTOMER_BATCH_SIZE = 100

# customer custom field that overrides the primary email for reminders and reports
REMINDER_EMAIL_FIELD = 'ReminderEmailAddress'

def get_customers_by_ids(customer_ids: list[str]) -> dict[str, dict]:
    """
    Look up customers by id. Returns {customer id: clean customer}; ids QBO doesn't
    return (e.g. deleted customers) are left out, so callers should use .get().
    """
    customer_ids = list(customer_ids)
    if not customer_ids:
        return {}

    realm_id = os.getenv("QBO_REALM_ID")
    access_token = get_access_token()

    customers = {}

    for start in range(0, len(customer_ids), CUSTOMER_BATCH_SIZE):
        batch = customer_ids[start:start + CUSTOMER_BATCH_SIZE]
        formatted_list = ", ".join([f"'{item}'" for item in batch])

        query_string = f"SELECT * FROM Customer WHERE Id IN ({formatted_list}) MAXRESULTS {CUSTOMER_BATCH_SIZE}"

        response = query(realm_id, access_token, query_string, CUSTOM_FIELDS_QUERY_PARAMS)

        for customer in response['QueryResponse'].get('Customer', []):
            customers[customer['Id']] = _clean_customer(customer)

    reminder_count = sum(1 for customer in customers.values() if customer['UsesReminderEmail'])
    logging.info(f"{reminder_count} of {len(customers)} customers have a {REMINDER_EMAIL_FIELD} set")

    return customers

def _clean_customer(customer: dict) -> dict:
    reminder_email = get_custom_field(customer, REMINDER_EMAIL_FIELD, f"customer {customer.get('DisplayName')}")
    reminder_email = reminder_email.strip() if isinstance(reminder_email, str) else None
    primary_email = customer.get('PrimaryEmailAddr', {}).get('Address')

    return {
        'Id': customer['Id'],
        'DisplayName': customer.get('DisplayName'),
        # where reports and reminders go: the reminder address when set, otherwise the
        # primary email. QBO allows several addresses here, separated by commas
        'Email': reminder_email or primary_email,
        'UsesReminderEmail': bool(reminder_email),
    }
