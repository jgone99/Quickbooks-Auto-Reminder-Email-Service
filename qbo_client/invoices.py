from qbo_client.auth import get_access_token
from qbo_client.client import query, QBOAPIError
from qbo_client.custom_fields import get_custom_field, CUSTOM_FIELDS_QUERY_PARAMS
import config  # loads .env
import os
from datetime import date
import logging

def get_open_invoices() -> list[dict]:
    # an invoice is open while it still has an unpaid balance
    return _get_invoices_where("WHERE Balance > '0'")

def _get_invoices_where(where_clause: str) -> list[dict]:
    realm_id = os.getenv("QBO_REALM_ID")
    access_token = get_access_token()

    invoice_count = query(realm_id, access_token, f"SELECT COUNT(*) FROM Invoice {where_clause}")['QueryResponse']['totalCount']

    raw_invoices = []
    start_position = 1

    while True:
        query_string = f"SELECT * FROM Invoice {where_clause} " \
        "ORDERBY MetaData.CreateTime " \
        f"STARTPOSITION {start_position} MAXRESULTS {config.QBO_MAX_RESULTS}"

        response = query(realm_id, access_token, query_string, CUSTOM_FIELDS_QUERY_PARAMS)

        raw_invoices_n = response['QueryResponse'].get('Invoice', [])

        if len(raw_invoices_n) == 0:
            break

        raw_invoices += raw_invoices_n
        start_position += len(raw_invoices_n)

    # fewer than counted means pages were missed: stop rather than email customers
    # an incomplete report. More than counted just means invoices changed mid-fetch
    if len(raw_invoices) < invoice_count:
        raise QBOAPIError(f"Incomplete fetch: QBO counted {invoice_count} invoices but only {len(raw_invoices)} were returned")

    if len(raw_invoices) > invoice_count:
        logging.warning(f"Fetched {len(raw_invoices)} invoices but QBO counted {invoice_count}, likely changed during the fetch")

    return _clean_invoices(raw_invoices)

def _clean_invoices(raw_invoices: list[dict]) -> list[dict]:
    clean_invoices = []

    for invoice in raw_invoices:
        due_date = invoice.get('DueDate')

        clean_invoice = {
            'Id': invoice.get('Id'),
            'DocNumber': invoice.get('DocNumber'),
            'CustomerId': invoice.get('CustomerRef', {}).get('value'),
            'CustomerName': invoice.get('CustomerRef', {}).get('name'),
            'CustomerPO': get_custom_field(invoice, 'Customer PO', f"invoice {invoice.get('DocNumber')}"),
            'TxnDate': invoice.get('TxnDate'),
            'DueDate': due_date,
            'TotalAmt': invoice.get('TotalAmt'),
            'Balance': invoice.get('Balance'),
            # None when the invoice has no due date
            'DaysUntilDue': (date.fromisoformat(due_date) - date.today()).days if due_date else None,
        }
        clean_invoices.append(clean_invoice)

    return clean_invoices
