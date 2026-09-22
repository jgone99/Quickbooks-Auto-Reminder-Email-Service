from collections import defaultdict
from pprint import pprint
from logger import setup_logging
import logging
import mimetypes

setup_logging()

from qbo_client.invoices import get_open_invoices
from qbo_client.customers import get_customers_by_ids
from spreadsheet import create_spreadsheet
from gmail_client.send import send_email

def build_report_by_customer(invoices: list[dict]) -> dict:
    reports = defaultdict(lambda: {
            "DueNextWeek": [],
            "Overdue": [],
            "Rest": [],
            "TotalOpenBalance": 0,
            "TotalOverdueBalance": 0,
            "DueNextWeekBalance": 0
        })
    for invoice in invoices:
        customer_id = invoice['CustomerRef']['value']
        report = reports[customer_id]
        days_until_due = invoice['DaysUntilDue']
        report['TotalOpenBalance'] += invoice['Balance']
        match days_until_due:
            case d if d < 0:
                report['Overdue'].append(invoice)
                report['TotalOverdueBalance'] += invoice['Balance']
            case d if d <= 7:
                report['DueNextWeek'].append(invoice)
                report['DueNextWeekBalance'] += invoice['Balance']
            case _:
                report['Rest'].append(invoice)
    return reports

def get_customer_details_from_ids(customer_ids: list[str]) -> dict:
    customers = get_customers_by_ids(customer_ids)
    customer_id_email_map = dict(
        { 
            customer['Id']: 
            { 
                'PrimaryEmailAddr': customer.get('PrimaryEmailAddr'),
                'DisplayName': customer.get('DisplayName')  
            } for customer in customers 
        }
    )
    return customer_id_email_map

def send_reminder_emails_by_customer(reports: dict, customer_details: dict):
    for customer_id, report in reports.items():
        customer_name = customer_details[customer_id]['DisplayName']
        customer_email = customer_details[customer_id]['PrimaryEmailAddr']

        if customer_email is None:
            logging.warning(f"No email on file for customer {customer_name} (ID {customer_id})")
            continue

        spreadsheet = create_spreadsheet(report)
        file_name = f"Invoice_Report_({customer_name}).xlsx"
        spreadsheet.save(file_name)

        result = send_email(customer_email, "", "", file_name)

        if result is not None:
            logging.info(f"Sent reminder to {customer_name} (ID {customer_id})")
        else:
            logging.error(f"Failed to send reminder to {customer_name} (ID {customer_id})")

logging.info("Start weekly report run")

open_invoices = get_open_invoices()
logging.info(f"Fetched {len(open_invoices)} open invoices")

by_customer_reports = build_report_by_customer(open_invoices)
logging.info(f"Grouped into {len(by_customer_reports)} customer reports")

customer_details = get_customer_details_from_ids(by_customer_reports.keys())
logging.info(f"Fetched details for {len(customer_details)} customers")

send_reminder_emails_by_customer(by_customer_reports, customer_details)

logging.info("Weekly report run complete")

# spreadsheet = create_spreadsheet(reports['9'])

# spreadsheet.save('test_spreadsheet.xlsx')