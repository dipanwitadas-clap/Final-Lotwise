# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


@frappe.whitelist()
def get_lots_by_mark(mark: str) -> dict:
	"""
	Fetch Tea Lots linked with the selected Mark
	"""
	if not mark:
		return {"mark": "", "lots": []}

	mark = mark.strip()

	lots = frappe.db.sql(
		"""
		SELECT
			name,
			lot_no,
			mark,
			grade,
			invoice_number,
			liquor_mark,
			acquisition_channel,
			purchase_date,
			packages,
			net_weight_total,
			rate,
			status,
			holding_status
		FROM `tabTea Lot`
		WHERE docstatus < 2
			AND mark = %(mark)s
		ORDER BY creation DESC
		""",
		{"mark": mark},
		as_dict=True,
	)

	return {"mark": mark, "lots": lots}


@frappe.whitelist()
def download_mark_xlsx(mark: str):
	"""
	Generate .xlsx with Tea Lots for a specific Mark and return as base64
	"""
	if not mark:
		return {"content": None, "filename": "Tea_Lots_Mark.xlsx"}

	mark = mark.strip()

	lots = frappe.db.sql(
		"""
		SELECT
			name,
			lot_no,
			mark,
			grade,
			invoice_number,
			liquor_mark,
			acquisition_channel,
			purchase_date,
			packages,
			net_weight_total,
			rate,
			status,
			holding_status
		FROM `tabTea Lot`
		WHERE docstatus < 2
			AND mark = %(mark)s
		ORDER BY creation DESC
		""",
		{"mark": mark},
		as_dict=True,
	)

	headers = [
		"Lot No",
		"Tea Lot ID",
		"Grade",
		"Invoice Number",
		"Liquor Mark",
		"Acquisition Channel",
		"Purchase Date",
		"Packages",
		"Net Weight Kg",
		"Rate",
		"Status",
		"Holding Status",
	]

	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = f"Tea Lots - {mark}"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=1, value=lot.lot_no)
		ws.cell(row=row_idx, column=2, value=lot.name)
		ws.cell(row=row_idx, column=3, value=lot.grade)
		ws.cell(row=row_idx, column=4, value=lot.invoice_number)
		ws.cell(row=row_idx, column=5, value=lot.liquor_mark)
		ws.cell(row=row_idx, column=6, value=lot.acquisition_channel)
		ws.cell(row=row_idx, column=7, value=str(lot.purchase_date) if lot.purchase_date else None)
		ws.cell(row=row_idx, column=8, value=lot.packages)
		ws.cell(row=row_idx, column=9, value=lot.net_weight_total)
		ws.cell(row=row_idx, column=10, value=lot.rate)
		ws.cell(row=row_idx, column=11, value=lot.status)
		ws.cell(row=row_idx, column=12, value=lot.holding_status)

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": f"Tea_Lots_Mark_{mark}.xlsx"}
