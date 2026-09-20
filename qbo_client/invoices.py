from qbo_client.auth import get_access_token
from qbo_client.client import query
from dotenv import load_dotenv
import os
from datetime import date

load_dotenv()

def get_open_invoices():
    realm_id = os.getenv("QBO_REALM_ID")
    access_token = get_access_token()
    query_string = "SELECT * FROM Invoice WHERE Balance > '0'"

    response = query(realm_id, access_token, query_string)

    raw_invoices = response['QueryResponse'].get('Invoice', [])

    clean_invoices = []

    for invoice in raw_invoices:
        clean_invoice = {
            'Id': invoice.get('Id'),
            'DocNumber': invoice.get('DocNumber'),
            'TxnDate': invoice.get('TxnDate'),
            'DueDate': invoice.get('DueDate'),
            'Balance': invoice.get('Balance'),
            'SalesTermRef': invoice.get('SalesTermRef'),
            'CustomerRef': invoice.get('CustomerRef'),
        }
        clean_invoice['DaysUntilDue'] = (date.fromisoformat(clean_invoice['DueDate']) - date.today()).days
        clean_invoices.append(clean_invoice)

    return clean_invoices