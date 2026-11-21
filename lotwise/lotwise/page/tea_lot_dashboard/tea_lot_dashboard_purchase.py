# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


def _purchase_rows() -> list:
	"""All Tea Purchases with PO details (data source for the Tea Purchase tab)."""
	return frappe.db.sql(
		"""
		SELECT
			tp.name AS tea_purchase,
			tp.tea_lot,
			tp.lot_no,
			tp.mark,
			tp.grade,
			tp.invoice_number,
			tp.acquisition_channel,
			tp.packages,
			tp.net_weight_total,
			tp.rate,
			tp.purchase_status,
			tp.purchase_order,
			po.status AS po_status,
			tp.broker,
			tp.warehouse,
			tp.sale_no
		FROM `tabTea Purchase` tp
		LEFT JOIN `tabPurchase Order` po ON po.name = tp.purchase_order
		WHERE tp.docstatus < 2
		ORDER BY tp.creation DESC
		""",
		as_dict=True,
	)


@frappe.whitelist()
def get_all_purchases() -> dict:
	return {"lots": _purchase_rows()}


@frappe.whitelist()
def download_purchases_xlsx():
	rows = _purchase_rows()
	columns = [
		("Tea Purchase ID", "tea_purchase"),
		("Tea Lot ID", "tea_lot"),
		("Lot No", "lot_no"),
		("Mark", "mark"),
		("Grade", "grade"),
		("Invoice No", "invoice_number"),
		("Channel", "acquisition_channel"),
		("Packages", "packages"),
		("Net Wt Kg", "net_weight_total"),
		("Purchase Rate", "rate"),
		("Purchase Status", "purchase_status"),
		("PO", "purchase_order"),
		("PO Status", "po_status"),
		("Broker", "broker"),
		("Warehouse", "warehouse"),
		("Sale No", "sale_no"),
	]
	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Tea Purchases"
	for ci, (header, _f) in enumerate(columns, 1):
		ws.cell(row=1, column=ci, value=header)
	for ri, row in enumerate(rows, 2):
		for ci, (_h, f) in enumerate(columns, 1):
			ws.cell(row=ri, column=ci, value=row.get(f))
	out = io.BytesIO()
	wb.save(out)
	return {
		"content": base64.b64encode(out.getvalue()).decode("utf-8"),
		"filename": "Tea_Purchases.xlsx",
	}
