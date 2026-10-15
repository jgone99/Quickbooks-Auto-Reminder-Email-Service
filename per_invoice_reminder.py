from logger import setup_logging
if __name__ == "__main__":
    # set up logging before anything else so even import and config errors are logged.
    # only when run as a script, so importing this module (e.g. from tests) doesn't write to logs/
    setup_logging()

from qbo_client.invoices import get_open_invoices
from qbo_client.customers import get_customers_by_ids
from datetime import date
from config import THRESHOLDS, THRESHOLD_TRACKER_PATH
import config
import json
import logging
import sys

def has_payment_term(invoice: dict) -> bool:
    # progress through the term can't be measured without a due date after the invoice date
    return bool(invoice['DueDate']) and invoice['DueDate'] > invoice['TxnDate']

def filter_out_below_threshold_invoices(threshold: float, invoices: list[dict]) -> list[dict]:
    filtered_invoices = []
    for invoice in invoices:
        txn_date = date.fromisoformat(invoice['TxnDate'])
        due_date = date.fromisoformat(invoice['DueDate'])
        elapsed_days = (date.today() - txn_date).days
        term_days = (due_date - txn_date).days
        if elapsed_days >= term_days * threshold:
            filtered_invoices.append(invoice)
    return filtered_invoices

def load_threshold_tracker() -> dict:
    if not THRESHOLD_TRACKER_PATH.exists() or THRESHOLD_TRACKER_PATH.stat().st_size == 0:
        return dict()

    # invalid JSON raises, so a corrupted tracker never gets silently replaced
    with THRESHOLD_TRACKER_PATH.open('r', encoding='utf-8') as file:
        return json.load(file)

def build_threshold_tracker(invoices: list[dict]) -> dict:
    tracker_object = dict()
    for invoice in invoices:
        invoice_id = invoice['Id']
        due_date = date.fromisoformat(invoice['DueDate'])
        txn_date = date.fromisoformat(invoice['TxnDate'])
        progression = (date.today() - txn_date) / (due_date - txn_date)
        met_thresholds = [t for t in THRESHOLDS if progression >= t]
        if met_thresholds:
            tracker_object[invoice_id] = max(met_thresholds)
    return tracker_object

def get_invoices_that_hit_new_threshold(invoices: list[dict], old_threshold_tracker: dict, new_threshold_tracker: dict) -> list[dict]:
    new_threshold_invoices = []
    for invoice in invoices:
        invoice_id = invoice['Id']
        new_threshold = new_threshold_tracker.get(invoice_id, -1)
        old_threshold = old_threshold_tracker.get(invoice_id, -1)
        if new_threshold > old_threshold:
            new_threshold_invoices.append(invoice)
    return new_threshold_invoices

def save_thresholds(thresholds: dict) -> None:
    with THRESHOLD_TRACKER_PATH.open('w', encoding='utf-8') as file:
        json.dump(thresholds, file, indent=4)

def extract_unique_customers_from_invoices(invoices: list[dict]) -> list[str]:
    return list({invoice['CustomerId'] for invoice in invoices})

def get_customer_email_mapping_from_ids(customer_ids: list[str]) -> dict:
    customers = get_customers_by_ids(customer_ids)
    return {customer_id: customer['Email'] for customer_id, customer in customers.items()}

def send_reminder_emails(invoices: list[dict], customer_id_email_map: dict):
    # TODO: not implemented yet
    pass

def main():
    invoices = [invoice for invoice in get_open_invoices() if has_payment_term(invoice)]
    logging.info(f"Fetched {len(invoices)} open invoices with a payment term")

    invoices = filter_out_below_threshold_invoices(THRESHOLDS[0], invoices)

    new_threshold_tracker = build_threshold_tracker(invoices)

    old_threshold_tracker = load_threshold_tracker()

    new_threshold_invoices = get_invoices_that_hit_new_threshold(invoices, old_threshold_tracker, new_threshold_tracker)
    logging.info(f"{len(new_threshold_invoices)} invoices reached a new threshold")

    if len(new_threshold_invoices) == 0:
        return

    customer_ids = extract_unique_customers_from_invoices(new_threshold_invoices)

    mapping = get_customer_email_mapping_from_ids(customer_ids)

    send_reminder_emails(new_threshold_invoices, mapping)

    # thresholds are only recorded once reminders really go out, otherwise
    # a dry run would use them up and the reminders would never be sent
    if config.DRY_RUN:
        logging.info("DRY_RUN is on: thresholds were not saved")
        return

    save_thresholds(new_threshold_tracker)

if __name__ == "__main__":
    try:
        config.validate()
        main()
    except Exception:
        logging.exception("Run failed")
        sys.exit(1)
