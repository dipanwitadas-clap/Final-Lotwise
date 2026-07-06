# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl
from frappe.model.document import Document
from frappe.utils import flt


class TeaLot(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		awr_date: DF.Date | None
		blend: DF.Literal["", "PREMIUM PACK"]
		broker: DF.Link | None
		centre: DF.Data | None
		certification: DF.Data | None
		chest_serial_range: DF.Data | None
		density: DF.Float
		division: DF.Data | None
		do_date: DF.Data | None
		do_reference: DF.Data | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		grade: DF.Link | None
		gross_wtpkg: DF.Float
		holding_status: DF.Literal["", "Committed", "Received", "In Stock"]
		intended_segment: DF.Link | None
		invoice_number: DF.Data
		liquor_mark: DF.Literal["", "A+", "A", "B+", "B", "C+", "C"]
		lot_no: DF.Data | None
		manufacturer_ref: DF.Data | None
		mark: DF.Link
		mfg_monthyear: DF.Data | None
		net_weight_total: DF.Float
		net_wtpkg: DF.Float
		packages: DF.Int
		packing: DF.Link | None
		purchase_date: DF.Date | None
		purchase_from: DF.Data | None
		purchase_invoice_date: DF.Date | None
		purchase_invoice_no: DF.Data | None
		rate: DF.Currency
		sale_no: DF.Data | None
		seller: DF.Link | None
		source_doctype: DF.Link | None
		source_doctype_id: DF.DynamicLink | None
		status: DF.Literal["", "Offered", "Evaluated"]
		total_amount_as_per_to_tax_invoice: DF.Float
		warehouse_name: DF.Data | None
		warehouselocation: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot"


# ============================================================
# XLSX DOWNLOAD - EVALUATION IMPORT
# ============================================================


@frappe.whitelist()
def download_evaluation_import_xlsx() -> dict:
	"""
	Generate xlsx with Tea Lots where status != 'Evaluated'.
	First 3 columns (Tea Lot, Mark, Invoice Number) have data,
	remaining columns have headers only (blank data).
	Returns base64 encoded content for frontend download.
	"""
	# Fetch unevaluated Tea Lots
	lots = frappe.db.sql(
		"""
		SELECT name, mark, invoice_number
		FROM `tabTea Lot`
		WHERE status != "Evaluated" OR status IS NULL
		ORDER BY creation DESC
		""",
		as_dict=True,
	)

	# Create workbook
	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Evaluations"

	# Headers matching tea_evaluation_import.xlsx format
	headers = [
		"Tea Lot",
		"Mark",
		"Invoice Number",
		"Taster",
		"Stage",
		"Liquor Mark",
		"Evaluation Date",
		"Colour",
		"Strength",
		"Taste",
		"Briskness",
		"Quality Grade",
		"Suggested Valuation",
		"Notes",
		"Evaluation Date",
	]

	# Write headers
	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	# Write data rows (only Tea Lot, Mark, Invoice Number filled)
	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=1, value=lot.name)
		ws.cell(row=row_idx, column=2, value=lot.mark)
		ws.cell(row=row_idx, column=3, value=lot.invoice_number)
		# Columns 4-14 remain blank (already None by default)

	# Save to BytesIO
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	# Encode to base64 for safe JSON transport
	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "tea_evaluation_import.xlsx"}
