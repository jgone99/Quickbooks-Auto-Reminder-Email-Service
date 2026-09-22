# current WIP: 
# trying to define extra spreadsheet columns that can be added with enum values.


from openpyxl import Workbook, worksheet
from enum import Enum, auto

class ExtraColumns(Enum):
    DUE_SOON = auto()
    DAYS_OVERDUE = auto()

_EXTRA_COLUMN_DEFS = {
    ExtraColumns.DUE_SOON: [("Days Until Due", lambda inv: inv["DaysUntilDue"])],
    ExtraColumns.DAYS_OVERDUE: [("Days Overdue", lambda inv: -inv["DaysUntilDue"])]
}

BASE_COLUMNS = [
    ('Invoice #', lambda inv: inv['DocNumber']),
    ('Due Date', lambda inv: inv['DueDate']),
    ('Balance', lambda inv: inv['Balance'])
]

def write_category_sheet(workbook: Workbook, sheet_name: str, invoices: list[dict], extra_columns: ExtraColumns) -> int:
    sheet = workbook.create_sheet(sheet_name)
    columns = BASE_COLUMNS + Extr

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

    write_category_sheet(workbook, "Open", report['Rest'])
    write_category_sheet(workbook, "Due Next Week", report['DueNextWeek'])
    write_category_sheet(workbook, "Overdue", report['Overdue'])
    return workbook
