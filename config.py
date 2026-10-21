import os
from pathlib import Path
from dotenv import load_dotenv

# all paths are anchored to the project folder so the scripts work no matter
# which directory they are launched from (e.g. Task Scheduler)
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
GMAIL_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN_PATH = PROJECT_ROOT / "token.json"
EMAIL_TEMPLATE_PATH = PROJECT_ROOT / "email_body_template.txt"
THRESHOLD_TRACKER_PATH = PROJECT_ROOT / "threshold_tracker.json"
SENT_LOG_PATH = PROJECT_ROOT / "sent_log.json"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# logs and reports are deleted once they are (retention - buffer) days old
MAX_LOG_RETENTION_DAYS = 30
MAX_LOG_RETENTION_BUFFER_DAYS = 1
MAX_REPORT_RETENTION_DAYS = MAX_LOG_RETENTION_DAYS
MAX_REPORT_RETENTION_BUFFER_DAYS = MAX_LOG_RETENTION_BUFFER_DAYS

load_dotenv(ENV_PATH)

QBO_BASE_URLS = {
    "sandbox": "https://sandbox-quickbooks.api.intuit.com",
    "production": "https://quickbooks.api.intuit.com",
}

QBO_ENVIRONMENT = os.getenv("QBO_ENVIRONMENT", "sandbox")
QBO_BASE_URL = QBO_BASE_URLS.get(QBO_ENVIRONMENT)

# must be set in .env for a run to start
REQUIRED_ENV_VARS = [
    "QBO_CLIENT_ID",
    "QBO_CLIENT_SECRET",
    "QBO_REDIRECT_URI",
    "QBO_REFRESH_TOKEN",
    "QBO_REALM_ID",
    # receives the log of every weekly run
    "RUN_LOG_RECIPIENT",
    "BUSINESS_NAME"
]

# when set in .env, every customer email goes to this address instead, so a live
# run can be checked end to end without emailing customers
TEST_RECIPIENT = os.getenv("TEST_RECIPIENT")

REQUEST_TIMEOUT_SECONDS = 30

# QBO caps a query at 1000 results per page
QBO_MAX_RESULTS = 1000

# shown in the email subject and body
BUSINESS_NAME = os.getenv("BUSINESS_NAME")
EMAIL_SUBJECT = f"Weekly Invoice Summary - {BUSINESS_NAME}"

# invoices due within this many days (and not yet overdue) count as "due soon"
DUE_SOON_DAYS = 7

# when True, emails are built but not sent. Reports are still saved to reports/ for review
DRY_RUN = True

# per_invoice_reminder.py: fractions of an invoice's payment term that trigger a reminder
THRESHOLDS = [0.5, 0.75, 0.8, 0.9, 1.0]

def validate():
    """
    Check that everything a run needs is in place, so a misconfiguration fails
    immediately with a clear message. Only names are reported, never values.
    """
    problems = []

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        problems.append(f"missing from .env: {', '.join(missing)}")

    if QBO_BASE_URL is None:
        problems.append(f"QBO_ENVIRONMENT must be one of {list(QBO_BASE_URLS)}, got '{QBO_ENVIRONMENT}'")

    if not GMAIL_CREDENTIALS_PATH.is_file():
        problems.append(f"Gmail credentials file not found: {GMAIL_CREDENTIALS_PATH}")

    # without a token, Gmail opens a browser to sign in, which hangs an unattended run
    if not DRY_RUN and not GMAIL_TOKEN_PATH.is_file():
        problems.append(f"Gmail token not found: {GMAIL_TOKEN_PATH}. Authorize Gmail once by hand before sending")

    if not EMAIL_TEMPLATE_PATH.is_file():
        problems.append(f"Email template not found: {EMAIL_TEMPLATE_PATH}")

    if problems:
        raise ValueError("Invalid configuration: " + "; ".join(problems))
