# current WIP: 
# 

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from enum import Enum

class ExtraColumn(Enum):
    DAYS_REMAINING = ("Days Until Due", lambda inv: inv["DaysUntilDue"])
    DAYS_OVERDUE = ("Days Overdue", lambda inv: -inv["DaysUntilDue"])

BASE_COLUMNS = [
    ('Invoice #', lambda inv: inv['DocNumber']),
    ('Due Date', lambda inv: inv['DueDate']),
    ('Balance', lambda inv: inv['Balance'])
]

BALANCE_COLUMN_INDEX = next(i for i, (title, _) in enumerate(BASE_COLUMNS) if title == 'Balance')

def create_sheet(workbook: Workbook, sheet_name: str) -> Worksheet:
    return workbook.create_sheet(sheet_name)

def write_category_sheet(workbook: Workbook, sheet_name: str, invoices: list[dict], extra_columns: list[ExtraColumn] = None) -> int:
    sheet = create_sheet(workbook, sheet_name)
    extra_columns = extra_columns or []
    columns = BASE_COLUMNS + [extra_column.value for extra_column in extra_columns]

    # setting the column titles including any extra ones from extra_columns
    for index, (title, _) in enumerate(columns, start=1):
        sheet.cell(row=1, column=index, value=title)

    for row_index, invoice in enumerate(invoices, start=2):
        for col_index, (_, get_inv_value) in enumerate(columns, start=1):
            sheet.cell(row=row_index, column=col_index, value=get_inv_value(invoice))

def create_spreadsheet(report: dict):
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    sheet1_name = "All Open Invoices"
    sheet2_name = "Due Next Week"
    sheet3_name = "Overdue Invoices"

    write_category_sheet(workbook, sheet1_name, report['Open'], [ExtraColumn.DAYS_REMAINING])
    write_category_sheet(workbook, sheet2_name, report['DueNextWeek'], [ExtraColumn.DAYS_REMAINING])
    write_category_sheet(workbook, sheet3_name, report['Overdue'], [ExtraColumn.DAYS_OVERDUE])

    balance_column_letter = chr(65 + BALANCE_COLUMN_INDEX)

    summary_sheet['A1'] = 'Open Balance'
    summary_sheet['A2'] = 'Due Next Week Balance'
    summary_sheet['A3'] = 'Overdue Balance'
    summary_sheet['B1'] = f"=SUM('{sheet1_name}'!{balance_column_letter}:{balance_column_letter})"
    summary_sheet['B2'] = f"=SUM('{sheet2_name}'!{balance_column_letter}:{balance_column_letter})"
    summary_sheet['B3'] = f"=SUM('{sheet3_name}'!{balance_column_letter}:{balance_column_letter})"

    return workbook
