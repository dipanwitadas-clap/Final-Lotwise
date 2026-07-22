# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


@frappe.whitelist()
def get_all_lots(from_date: str | None = None, to_date: str | None = None) -> dict:
	"""
	Fetch all Tea Lots for the main Tea Lot tab.
	Optional date range filter on purchase_date.
	"""
	conditions = ["docstatus < 2"]
	values = {}

	if from_date:
		conditions.append("purchase_date >= %(from_date)s")
		values["from_date"] = from_date

	if to_date:
		conditions.append("purchase_date <= %(to_date)s")
		values["to_date"] = to_date

	lots = frappe.db.sql(
		f"""
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
			purchase_status,
			seller,
			warehouselocation AS warehouse,
			auction_centre
		FROM `tabTea Lot`
		WHERE {" AND ".join(conditions)}
		ORDER BY creation DESC
		""",
		values,
		as_dict=True,
	)

	return {"lots": lots}


@frappe.whitelist()
def download_all_lots_xlsx():
	"""
	Generate .xlsx with all Tea Lots and return as base64
	"""
	# Get all lots (same query as get_all_lots)
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
			purchase_status,
			seller,
			warehouselocation AS warehouse,
			auction_centre
		FROM `tabTea Lot`
		WHERE docstatus < 2
		ORDER BY creation DESC
		""",
		as_dict=True,
	)

	headers = [
		"Tea Lot ID",
		"Lot No",
		"Mark",
		"Grade",
		"Invoice No",
		"Liquor Mark",
		"Channel",
		"Purchase Date",
		"Packages",
		"Net Wt Kg",
		"Rate",
		"Status",
		"Purchase Status",
		"Seller",
		"Warehouse",
		"Auction Centre",
	]

	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Tea Lots"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=1, value=lot.name)
		ws.cell(row=row_idx, column=2, value=lot.lot_no)
		ws.cell(row=row_idx, column=3, value=lot.mark)
		ws.cell(row=row_idx, column=4, value=lot.grade)
		ws.cell(row=row_idx, column=5, value=lot.invoice_number)
		ws.cell(row=row_idx, column=6, value=lot.liquor_mark)
		ws.cell(row=row_idx, column=7, value=lot.acquisition_channel)
		ws.cell(row=row_idx, column=8, value=str(lot.purchase_date) if lot.purchase_date else None)
		ws.cell(row=row_idx, column=9, value=lot.packages)
		ws.cell(row=row_idx, column=10, value=lot.net_weight_total)
		ws.cell(row=row_idx, column=11, value=lot.rate)
		ws.cell(row=row_idx, column=12, value=lot.status)
		ws.cell(row=row_idx, column=13, value=lot.purchase_status)
		ws.cell(row=row_idx, column=14, value=lot.seller)
		ws.cell(row=row_idx, column=15, value=lot.warehouse)
		ws.cell(row=row_idx, column=16, value=lot.auction_centre)

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "Tea_Lots.xlsx"}
