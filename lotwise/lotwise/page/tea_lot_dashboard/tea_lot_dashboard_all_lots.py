# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


def _lot_rows() -> list:
	"""All Tea Lots (the data source for the Tea Lot tab)."""
	return frappe.db.sql(
		"""
		SELECT
			name,
			tea_purchase,
			lot_no,
			mark,
			grade,
			invoice_number,
			acquisition_channel,
			packages,
			net_weight_total,
			rate,
			purchase_status,
			warehouse,
			auction_centre,
			sale_no
		FROM `tabTea Lot`
		WHERE docstatus < 2
		ORDER BY creation DESC
		""",
		as_dict=True,
	)


@frappe.whitelist()
def get_all_lots() -> dict:
	"""
	Fetch all Tea Lots for the main Tea Lot tab.
	"""
	return {"lots": _lot_rows()}


@frappe.whitelist()
def download_all_lots_xlsx():
	"""
	Generate .xlsx with all Tea Lots and return as base64
	"""
	lots = _lot_rows()

	columns = [
		("Tea Lot ID", "name"),
		("Tea Purchase ID", "tea_purchase"),
		("Lot No", "lot_no"),
		("Mark", "mark"),
		("Grade", "grade"),
		("Invoice No", "invoice_number"),
		("Channel", "acquisition_channel"),
		("Packages", "packages"),
		("Net Wt Kg", "net_weight_total"),
		("Purchase Rate", "rate"),
		("Purchase Status", "purchase_status"),
		("Warehouse", "warehouse"),
		("Auction Centre", "auction_centre"),
		("Sale No", "sale_no"),
	]

	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Tea Lots"

	for col_idx, (header, _fieldname) in enumerate(columns, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, lot in enumerate(lots, 2):
		for col_idx, (_header, fieldname) in enumerate(columns, 1):
			ws.cell(row=row_idx, column=col_idx, value=lot.get(fieldname))

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "Tea_Lots.xlsx"}
