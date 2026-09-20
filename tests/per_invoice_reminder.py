from qbo_client.invoices import get_open_invoices
from qbo_client.customers import get_customers_by_ids
from datetime import date
from config import THRESHOLDS
from pathlib import Path
import json
import os

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
    try:
        file_path = Path('threshold_tracker.json')
        if os.path.getsize(file_path) > 0:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = dict()
    except FileNotFoundError:
        file_path.touch(exist_ok=False)
        data = dict()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON syntax. Details: {e}")
        raise e
    return data

def build_threshold_tracker(invoices: list[dict]) -> list[dict]:
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
    try:
        file_path = Path('threshold_tracker.json')
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(thresholds, file, indent=4)
    except FileNotFoundError as e:
        print(f"Error: File {file_path} not found")
        raise e

def extract_unique_customers_from_invoices(invoices: list[dict]) -> list[dict]:
    customers = list(map(lambda x: x['CustomerRef']['value'], invoices))
    return list(set(customers))

def get_customer_email_mapping_from_ids(customer_ids: list[str]) -> dict:
    customers = get_customers_by_ids(customer_ids)
    customer_id_email_map = dict({ customer['Id']: customer['PrimaryEmailAddr'] for customer in customers })
    return customer_id_email_map

def send_reminder_emails(invoices: list[dict], customer_id_email_map: dict):
    final_tracker = dict(old_threshold_tracker)

invoices = get_open_invoices()

invoices = filter_out_below_threshold_invoices(THRESHOLDS[0], invoices)

new_threshold_tracker = build_threshold_tracker(invoices)

old_threshold_tracker = load_threshold_tracker()

new_threshold_invoices = get_invoices_that_hit_new_threshold(invoices, old_threshold_tracker, new_threshold_tracker)

print(new_threshold_invoices)

if len(new_threshold_invoices) > 0:
    customer_ids = extract_unique_customers_from_invoices(new_threshold_invoices)

    mapping = get_customer_email_mapping_from_ids(customer_ids)

    save_thresholds(new_threshold_tracker)

    

