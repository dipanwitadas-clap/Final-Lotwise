# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


@frappe.whitelist()
def get_lots_by_grade(grade: str) -> dict:
	"""
	Fetch Tea Lots linked with the selected Grade
	"""
	if not grade:
		return {"grade": "", "lots": []}

	grade = grade.strip()

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
			AND grade = %(grade)s
		ORDER BY creation DESC
		""",
		{"grade": grade},
		as_dict=True,
	)

	return {"grade": grade, "lots": lots}


@frappe.whitelist()
def download_grade_xlsx(grade: str):
	"""
	Generate .xlsx with Tea Lots for a specific Grade and return as base64
	"""
	if not grade:
		return {"content": None, "filename": "Tea_Lots_Grade.xlsx"}

	grade = grade.strip()

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
			AND grade = %(grade)s
		ORDER BY creation DESC
		""",
		{"grade": grade},
		as_dict=True,
	)

	headers = [
		"Lot No",
		"Tea Lot ID",
		"Mark",
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
	ws.title = f"Tea Lots - {grade}"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=1, value=lot.lot_no)
		ws.cell(row=row_idx, column=2, value=lot.name)
		ws.cell(row=row_idx, column=3, value=lot.mark)
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

	return {"content": encoded, "filename": f"Tea_Lots_Grade_{grade}.xlsx"}
