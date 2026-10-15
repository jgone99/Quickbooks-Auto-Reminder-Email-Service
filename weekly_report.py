from logger import setup_logging
if __name__ == "__main__":
    # set up logging before anything else so even import and config errors are logged.
    # only when run as a script, so importing this module (e.g. from tests) doesn't write to logs/
    setup_logging()

from qbo_client.invoices import get_open_invoices
from qbo_client.customers import get_customers_by_ids
from gmail_client.auth import get_gmail_service
from gmail_client.client import send_message
from report_builder import build_reports_by_customer
import config
import report_email
import report_workbook
import sent_log
import status_email
import logging
import sys

def main():
    if config.DRY_RUN:
        logging.info("DRY_RUN is on: reports are saved but no emails are sent")
    else:
        # connect before doing any work, so a Gmail problem fails the run once
        # with a clear error instead of once per customer
        get_gmail_service()

        if config.TEST_RECIPIENT:
            logging.info(f"TEST_RECIPIENT is set: all customer emails go to {config.TEST_RECIPIENT}")

    invoices = get_open_invoices()
    logging.info(f"Fetched {len(invoices)} open invoices")

    reports = build_reports_by_customer(invoices)
    logging.info(f"Grouped into {len(reports)} customer reports")

    customers = get_customers_by_ids(reports.keys())
    logging.info(f"Fetched details for {len(customers)} customers")

    already_sent = sent_log.load_sent_this_week()
    if already_sent:
        logging.info(f"{len(already_sent)} customers were already sent this week's report and will be skipped")

    sent, skipped, failed = 0, 0, 0

    for customer_id, report in reports.items():
        customer = customers.get(customer_id)

        if customer is None:
            logging.warning(f"Customer {customer_id} has open invoices but was not returned by QBO, skipping")
            skipped += 1
            continue

        if not customer['Email']:
            logging.warning(f"No email on file for customer {customer['DisplayName']} (ID {customer_id}), skipping")
            skipped += 1
            continue

        if customer_id in already_sent:
            skipped += 1
            continue

        # one customer failing must not stop the rest from getting their report
        try:
            _send_report(customer, report)
            sent += 1
        except Exception:
            logging.exception(f"Failed to send report to {customer['DisplayName']} (ID {customer_id})")
            failed += 1

    action = "Prepared" if config.DRY_RUN else "Sent"
    logging.info(f"{action} {sent} reports, skipped {skipped}, failed {failed}")

    if failed:
        raise RuntimeError(f"{failed} of {len(reports)} customer reports failed, see log for details")

    logging.info("Run finished")

def _send_report(customer: dict, report: dict):
    path = report_workbook.save_report(report, customer['DisplayName'])
    message = report_email.build_report_message(customer, report, path)

    if config.DRY_RUN:
        redirect = f", redirected to {message['To']}" if config.TEST_RECIPIENT else ""
        logging.info(f"[dry run] Would send {path.name} to {customer['DisplayName']} ({customer['Email']}{redirect})")
        return

    send_message(message)

    # test sends don't count, so the real run that week still emails the customer
    if not config.TEST_RECIPIENT:
        sent_log.record_sent(customer['Id'])

if __name__ == "__main__":
    # runs every time, alongside the log cleanup in setup_logging, so reports keep to the
    # retention limit even when the run fails. It logs its own errors and never raises
    report_workbook.cleanup_old_reports()

    succeeded = False

    try:
        config.validate()
        main()
        succeeded = True
    except Exception:
        logging.exception("Run failed")
    finally:
        status_email.send_run_log(succeeded)

    if not succeeded:
        sys.exit(1)
