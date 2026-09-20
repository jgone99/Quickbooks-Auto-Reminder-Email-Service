from openpyxl import Workbook, worksheet

def write_category_sheet(workbook: Workbook, sheet_name: str, invoices: list[dict]) -> int:
    sheet = workbook.create_sheet(sheet_name)
    sheet["A1"] = "Invoice #"
    sheet["B1"] = "Due Date"
    sheet["C1"] = "Balance"

    for i, invoice in enumerate(invoices):
        row = i + 2
        sheet.cell(row=row, column=1, value=invoice['DocNumber'])
        sheet.cell(row=row, column=2, value=invoice['DueDate'])
        sheet.cell(row=row, column=3, value=invoice['Balance'])

def create_spreadsheet(report: dict):
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    write_category_sheet(workbook, "Open", report['Rest'])
    write_category_sheet(workbook, "Due Next Week", report['DueNextWeek'])
    write_category_sheet(workbook, "Overdue", report['Overdue'])
    return workbook
