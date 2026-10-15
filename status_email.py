import logging
import os
from datetime import date
from gmail_client.client import build_message, send_message
import config
import logger

def send_run_log(succeeded: bool):
    """
    Email this run's log file to RUN_LOG_RECIPIENT. Never raises, since it runs
    after the outcome of the run is already decided.
    """
    recipient = os.getenv("RUN_LOG_RECIPIENT")

    # sending would open a browser to sign in without a token, hanging the run
    if config.DRY_RUN or not recipient or not config.GMAIL_TOKEN_PATH.is_file():
        logging.info("Run log was not emailed (dry run, no RUN_LOG_RECIPIENT, or no Gmail token)")
        return

    status = "succeeded" if succeeded else "FAILED"

    try:
        message = build_message(
            to=recipient,
            subject=f"Weekly invoice report run {status} - {date.today():%m/%d/%Y}",
            body=f"The weekly invoice report run {status}. The log is attached.",
            attachment_path=logger.log_path,
        )
        send_message(message)
    except Exception:
        logging.exception("Failed to email the run log")
