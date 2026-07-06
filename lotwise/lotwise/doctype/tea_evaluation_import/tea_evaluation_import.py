# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import re
from datetime import date, datetime

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

# ==========================================================
# EXCEL COLUMN MAPPING
# ==========================================================


HEADER_TO_FIELD = {
	"tea lot": {"field": "tea_lot", "type": "str"},
	"taster": {"field": "taster", "type": "str"},
	"stage": {"field": "stage", "type": "str"},
	"liquor mark": {"field": "liquor_mark", "type": "str"},
	"evaluation date": {"field": "evaluation_date", "type": "date"},
	"colour": {"field": "colour", "type": "float"},
	"strength": {"field": "strength", "type": "float"},
	"taste": {"field": "taste", "type": "float"},
	"briskness": {"field": "briskness", "type": "float"},
	"quality grade": {"field": "quality_grade", "type": "str"},
	"suggested valuation": {"field": "suggested_valuation", "type": "float"},
	"notes": {"field": "notes", "type": "str"},
	"invoice number": {"field": "invoice_number", "type": "str"},
	"mark": {"field": "mark", "type": "str"},
}


# ==========================================================
# HELPERS
# ==========================================================


def normalize(value):
	if value is None:
		return ""

	return re.sub(r"[^a-z0-9]+", " ", str(value).lower().strip()).strip()


def convert_value(value, field_type):
	if field_type == "date":
		if not value:
			return None

		# If openpyxl already parsed it as a datetime/date object, use it directly
		if isinstance(value, (datetime, date)):
			return value

		# If it's a string, try DD-MM-YYYY first (common Indian format)
		# to avoid day/month swapping
		if isinstance(value, str):
			value = value.strip()

			# Try DD-MM-YYYY or DD/MM/YYYY
			for sep in ("-", "/", "."):
				parts = value.split(sep)

				if len(parts) == 3 and len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
					day, month, year = parts

					if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
						return date(int(year), int(month), int(day))

		# Fallback to Frappe's getdate (which uses MM-DD-YYYY)
		return getdate(value)

	if field_type == "float":
		return flt(value) if value else 0

	return str(value).strip() if value else None


# ==========================================================
# EXCEL READING
# ==========================================================


def find_header_row(ws):
	for row in range(1, min(ws.max_row, 50) + 1):
		headers = []

		for col in range(1, ws.max_column + 1):
			headers.append(normalize(ws.cell(row, col).value))

		if "tea lot" in headers and "taster" in headers and "stage" in headers:
			return row

	frappe.throw(_("Excel header not found"))


def get_column_map(ws, header_row):
	column_map = {}

	for col in range(1, ws.max_column + 1):
		header = normalize(ws.cell(header_row, col).value)

		if header in HEADER_TO_FIELD:
			column_map[col] = HEADER_TO_FIELD[header]

	return column_map


def read_excel_rows(ws, column_map, start_row):
	rows = []

	for row in range(start_row, ws.max_row + 1):
		data = {"row_status": "Pending"}

		has_data = False

		for col, config in column_map.items():
			value = convert_value(ws.cell(row, col).value, config["type"])

			data[config["field"]] = value

			if value:
				has_data = True

		if has_data:
			rows.append(data)

	return rows


# ==========================================================
# DOCTYPE
# ==========================================================


class TeaEvaluationImport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.tea_evaluation_import_item.tea_evaluation_import_item import (
			TeaEvaluationImportItem,
		)

		computed_total_evaluations: DF.Int
		evaluation_import_date: DF.Date | None
		import_file: DF.Attach
		items: DF.Table[TeaEvaluationImportItem]
		rows_created: DF.Int
		rows_duplicate: DF.Int
		rows_error: DF.Int
		rows_parsed: DF.Int
	# end: auto-generated types

	# ======================================================
	# LOAD EXCEL DATA BUTTON
	# ======================================================

	@frappe.whitelist()
	def load_excel_data(self):
		if not self.import_file:
			frappe.throw(_("Please upload XLSX file"))

		file_doc = frappe.get_doc("File", {"file_url": self.import_file})

		wb = openpyxl.load_workbook(file_doc.get_full_path(), data_only=True)

		ws = wb[wb.sheetnames[0]]

		header_row = find_header_row(ws)

		column_map = get_column_map(ws, header_row)

		rows = read_excel_rows(ws, column_map, header_row + 1)

		self.set("items", [])

		for row in rows:
			self.append("items", row)

		self.rows_parsed = len(rows)

		self.computed_total_evaluations = len(rows)

		self.save()

		return {"rows": len(rows)}

	# ======================================================
	# CREATE TEA EVALUATION BUTTON
	# ======================================================

	@frappe.whitelist()
	def create_evaluations(self):
		created = 0

		errors = 0

		duplicates = 0

		for row in self.items:
			if row.row_status == "Created":
				continue

			try:
				if not row.tea_lot or not row.taster or not row.stage:
					row.row_status = "Error"

					row.message = "Tea Lot, Taster and Stage required"

					errors += 1

					continue

				if not frappe.db.exists("Tea Lot", row.tea_lot):
					row.row_status = "Error"

					row.message = f"Tea Lot {row.tea_lot} not found"

					errors += 1

					continue

				if not frappe.db.exists("Taster", row.taster):
					row.row_status = "Error"

					row.message = f"Taster {row.taster} not found"

					errors += 1

					continue

				if self.is_duplicate(row.tea_lot, row.taster, row.stage, row.evaluation_date):
					row.row_status = "Duplicate"

					row.message = "Duplicate Evaluation"

					duplicates += 1

					continue

				doc = frappe.get_doc(
					{
						"doctype": "Tea Evaluation",
						"tea_lot": row.tea_lot,
						"taster": row.taster,
						"stage": row.stage,
						"evaluation_date": row.evaluation_date or self.evaluation_date,
						"liquor_mark": row.liquor_mark,
						"colour": flt(row.colour),
						"strength": flt(row.strength),
						"taste": flt(row.taste),
						"briskness": flt(row.briskness),
						"quality_grade": row.quality_grade,
						"suggested_valuation": flt(row.suggested_valuation),
						"notes": row.notes,
						"invoice_number": row.invoice_number,
						"mark": row.mark,
					}
				)

				doc.insert(ignore_permissions=True)

				row.row_status = "Created"

				row.message = doc.name

				created += 1

			except Exception as e:
				row.row_status = "Error"

				row.message = str(e)[:140]

				errors += 1

				frappe.log_error(frappe.get_traceback(), "Tea Evaluation Creation Error")

		self.rows_created = created

		self.rows_error = errors

		self.rows_duplicate = duplicates

		self.save()

		return {"created": created, "errors": errors, "duplicates": duplicates}

	# ======================================================
	# DUPLICATE CHECK
	# ======================================================

	def is_duplicate(self, tea_lot, taster, stage, evaluation_date):
		if not evaluation_date:
			return False

		exists = frappe.get_all(
			"Tea Evaluation",
			filters={
				"tea_lot": tea_lot,
				"taster": taster,
				"stage": stage,
				"evaluation_date": getdate(evaluation_date),
			},
		)

		return bool(exists)
