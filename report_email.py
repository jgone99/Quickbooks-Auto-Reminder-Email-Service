from email.message import EmailMessage
from pathlib import Path
from gmail_client.client import build_message
import config

def build_report_message(customer: dict, report: dict, attachment_path: Path) -> EmailMessage:
    to = customer['Email']
    subject = config.EMAIL_SUBJECT

    if config.TEST_RECIPIENT:
        subject = f"[TEST for {to}] {subject}"
        to = config.TEST_RECIPIENT

    return build_message(
        to=to,
        subject=subject,
        body=build_body(customer['DisplayName'], report),
        attachment_path=attachment_path,
    )

def build_body(customer_name: str, report: dict) -> str:
    template = config.EMAIL_TEMPLATE_PATH.read_text(encoding="utf-8")

    return template.format(
        customer_name=customer_name,
        business_name=config.BUSINESS_NAME,
        due_soon_days=config.DUE_SOON_DAYS,
        total_balance=_money(report['OpenBalance']),
        due_soon_balance=_money(report['DueSoonBalance']),
        overdue_balance=_money(report['OverdueBalance']),
    )

def _money(amount: float) -> str:
    return f"{amount:,.2f}"
