import logging
import re
from datetime import date
from pathlib import Path
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from retention import delete_expired_files
import config

# e.g. 2026-10-14_Invoice_Report_Acme_Corp.xlsx
REPORT_NAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_Invoice_Report_.+\.xlsx$")

SUMMARY_SHEET_NAME = "Summary"
OPEN_SHEET_NAME = "All Open Invoices"
DUE_SOON_SHEET_NAME = f"Due Within {config.DUE_SOON_DAYS} Days"
OVERDUE_SHEET_NAME = "Overdue Invoices"

DATE_FORMAT = "mm/dd/yyyy"
CURRENCY_FORMAT = '"$"#,##0.00'

# each column is (title, value getter, number format)
COLUMNS = [
    ('Invoice #', lambda inv: inv['DocNumber'], None),
    ('Due Date', lambda inv: date.fromisoformat(inv['DueDate']) if inv['DueDate'] else None, DATE_FORMAT),
    ('PO #', lambda inv: inv['CustomerPO'], None),
    ('Balance', lambda inv: inv['Balance'], CURRENCY_FORMAT),
]

BALANCE_COLUMN = xl_col_to_name(next(i for i, (title, _, _) in enumerate(COLUMNS) if title == 'Balance'))

COLUMN_WIDTH = 16

def save_report(report: dict, customer_name: str) -> Path:
    """
    Write the customer's report to reports/ and return its path.
    """
    config.REPORTS_DIR.mkdir(exist_ok=True)
    path = config.REPORTS_DIR / f"{date.today():%Y-%m-%d}_Invoice_Report_{_safe_file_name(customer_name)}.xlsx"

    # the file is written when the context exits
    with xlsxwriter.Workbook(path) as workbook:
        formats = {
            'bold': workbook.add_format({'bold': True}),
            DATE_FORMAT: workbook.add_format({'num_format': DATE_FORMAT}),
            CURRENCY_FORMAT: workbook.add_format({'num_format': CURRENCY_FORMAT}),
        }

        # added first so it's the sheet the file opens on
        summary_sheet = workbook.add_worksheet(SUMMARY_SHEET_NAME)

        _write_category_sheet(workbook, formats, OPEN_SHEET_NAME, report['Open'])
        _write_category_sheet(workbook, formats, DUE_SOON_SHEET_NAME, report['DueSoon'])
        _write_category_sheet(workbook, formats, OVERDUE_SHEET_NAME, report['Overdue'])

        summary_rows = [
            ('Open Balance', OPEN_SHEET_NAME, report['OpenBalance']),
            (f'Due Within {config.DUE_SOON_DAYS} Days', DUE_SOON_SHEET_NAME, report['DueSoonBalance']),
            ('Overdue Balance', OVERDUE_SHEET_NAME, report['OverdueBalance']),
        ]

        for row, (label, sheet_name, total) in enumerate(summary_rows):
            summary_sheet.write(row, 0, label, formats['bold'])
            # the total is stored with the formula so previews that don't recalculate
            # (Gmail, phones) still show it instead of a blank cell
            summary_sheet.write_formula(row, 1, f"=SUM('{sheet_name}'!{BALANCE_COLUMN}:{BALANCE_COLUMN})", formats[CURRENCY_FORMAT], total)

        summary_sheet.set_column(0, 0, 24)
        summary_sheet.set_column(1, 1, COLUMN_WIDTH)

    return path

def _write_category_sheet(workbook: xlsxwriter.Workbook, formats: dict, sheet_name: str, invoices: list[dict]):
    sheet = workbook.add_worksheet(sheet_name)

    for col_index, (title, _, _) in enumerate(COLUMNS):
        sheet.write(0, col_index, title, formats['bold'])

    for row_index, invoice in enumerate(invoices, start=1):
        for col_index, (_, get_value, number_format) in enumerate(COLUMNS):
            sheet.write(row_index, col_index, get_value(invoice), formats.get(number_format))

    sheet.set_column(0, len(COLUMNS) - 1, COLUMN_WIDTH)

    # keep the titles visible while scrolling
    sheet.freeze_panes(1, 0)

def cleanup_old_reports():
    # housekeeping must never stop a run
    try:
        if config.REPORTS_DIR.exists():
            delete_expired_files(config.REPORTS_DIR, REPORT_NAME_PATTERN, config.MAX_REPORT_RETENTION_DAYS, config.MAX_REPORT_RETENTION_BUFFER_DAYS, "report")
    except Exception:
        logging.exception("Report cleanup failed")

def _safe_file_name(name: str) -> str:
    # customer names can contain characters that aren't allowed in file names
    return re.sub(r"[^\w-]+", "_", name).strip("_")
