from collections import defaultdict
import config

def _empty_report() -> dict:
    return {
        "Open": [],
        "DueSoon": [],
        "Overdue": [],
        "OpenBalance": 0,
        "DueSoonBalance": 0,
        "OverdueBalance": 0,
    }

def build_reports_by_customer(invoices: list[dict]) -> dict[str, dict]:
    """
    Group open invoices into one report per customer id. Every invoice is in "Open";
    it is also in "Overdue" once past due, or "DueSoon" when due within DUE_SOON_DAYS.
    Invoices with no due date are only counted as open.
    """
    reports = defaultdict(_empty_report)

    for invoice in invoices:
        report = reports[invoice['CustomerId']]
        balance = invoice['Balance']
        days_until_due = invoice['DaysUntilDue']

        report['Open'].append(invoice)
        report['OpenBalance'] += balance

        match days_until_due:
            case None:
                pass
            case d if d < 0:
                report['Overdue'].append(invoice)
                report['OverdueBalance'] += balance
            case d if d <= config.DUE_SOON_DAYS:
                report['DueSoon'].append(invoice)
                report['DueSoonBalance'] += balance

    # summing floats leaves values like 1234.5000000001
    for report in reports.values():
        for key in ("OpenBalance", "DueSoonBalance", "OverdueBalance"):
            report[key] = round(report[key], 2)

    return dict(reports)
