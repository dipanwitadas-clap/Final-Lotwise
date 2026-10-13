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
	"stage": {"field": "evaluation_stage", "type": "str"},
	"liquor mark": {"field": "liquor_mark", "type": "str"},
	"evaluation date dd mm yyyy": {"field": "evaluation_date", "type": "date"},
	"colour": {"field": "colour", "type": "int"},
	"strength": {"field": "strength", "type": "int"},
	"taste": {"field": "taste", "type": "int"},
	"briskness": {"field": "briskness", "type": "int"},
	"quality grade": {"field": "quality_grade", "type": "str"},
	"suggested valuation": {"field": "suggested_valuation", "type": "float"},
	"actual valuation": {"field": "actual_valuation", "type": "float"},
	"notes": {"field": "notes", "type": "str"},
	"invoice number": {"field": "invoice_number", "type": "str"},
	"mark": {"field": "mark", "type": "str"},
	"lot no": {"field": "lot_no", "type": "str"},
	"purchase status": {"field": "purchase_status", "type": "str"},
	"grade": {"field": "grade", "type": "str"},
	"density": {"field": "density", "type": "float"},
	"liquor mark tea lot": {"field": "lot_liquor_mark", "type": "str"},
	"purchase date dd mm yyyy": {"field": "purchase_date", "type": "date"},
	"evaluation status": {"field": "evaluation_status", "type": "str"},
	"sale no": {"field": "sale_no", "type": "int"},
	"auction centre": {"field": "auction_centre", "type": "str"},
}

# ==========================================================
# DYNAMIC SELECT OPTIONS HELPER
# ==========================================================


def get_tea_evaluation_link_doctype(fieldname):
	"""Return the Link target doctype for a Tea Evaluation field, if it is a Link field."""
	meta = frappe.get_meta("Tea Evaluation")
	field = meta.get_field(fieldname)
	if not field or field.fieldtype != "Link" or not field.options:
		return None
	return field.options


def is_valid_tea_evaluation_link_value(fieldname, value):
	"""Check whether value exists in the doctype linked by a Tea Evaluation Link field."""
	link_doctype = get_tea_evaluation_link_doctype(fieldname)
	if not link_doctype:
		return False
	return bool(frappe.db.exists(link_doctype, value))


def get_tea_evaluation_mandatory_fields():
	"""Dynamically fetch mandatory (reqd) field names from Tea Evaluation doctype."""
	meta = frappe.get_meta("Tea Evaluation")
	mandatory = []
	for field in meta.fields:
		if field.get("reqd") and field.get("fieldname"):
			mandatory.append(field.get("fieldname"))
	return mandatory


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

	if field_type == "int":
		if value is None or value == "":
			return None
		try:
			return int(float(str(value).strip()))
		except (ValueError, TypeError):
			return None

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
# VALIDATION HELPER
# ==========================================================


def validate_import_row(row):
	"""Validate a single import row's Link and Select fields.
	Sets row_status = 'Error' with a clear message if invalid.
	Returns True if valid, False if invalid.
	"""
	# Validate Link fields: check if value exists in DB
	for link_field, link_doctype in [("tea_lot", "Tea Lot"), ("taster", "Taster"), ("mark", "Mark")]:
		value = row.get(link_field)
		if value:
			if not frappe.db.exists(link_doctype, value):
				row["row_status"] = "Error"
				row["message"] = f"Invalid {link_field}: '{value}' not found in {link_doctype}"
				return False

	# Validate Link fields on Tea Evaluation: check if value exists in the linked doctype
	for link_field, label in [
		("evaluation_stage", "Stage"),
		("liquor_mark", "Liquor Mark"),
		("quality_grade", "Quality Grade"),
	]:
		value = row.get(link_field)
		if value and not is_valid_tea_evaluation_link_value(link_field, value):
			row["row_status"] = "Error"
			row["message"] = f"Invalid {label}: '{value}' is not a valid option"
			return False

	# Validate date field
	eval_date = row.get("evaluation_date")
	if eval_date and not isinstance(eval_date, (date, datetime)):
		row["row_status"] = "Error"
		row["message"] = f"Invalid Evaluation Date: '{eval_date}' is not a valid date"
		return False

	return True


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

		# --- First pass: validate ALL rows and collect ALL errors ---
		all_errors = []
		for row in rows:
			row_errors = []
			tea_lot_value = row.get("tea_lot")
			taster_value = row.get("taster")
			mark_value = row.get("mark")

			# Validate all Link fields
			if tea_lot_value and not frappe.db.exists("Tea Lot", tea_lot_value):
				row_errors.append(f"Tea Lot '{tea_lot_value}' not found")

			if taster_value and not frappe.db.exists("Taster", taster_value):
				row_errors.append(f"Taster '{taster_value}' not found")

			if mark_value and not frappe.db.exists("Mark", mark_value):
				row_errors.append(f"Mark '{mark_value}' not found")

			if row_errors:
				all_errors.append(
					"Tea Lot {0}: {1}".format(tea_lot_value or "(blank)", ", ".join(row_errors))
				)

		# --- If ANY error exists, abort ---
		if all_errors:
			self.save()
			frappe.throw(
				_(
					"Cannot load data due to validation errors. Please fix the following and try again:<br>{0}"
				).format("<br>".join(f"- {r}" for r in all_errors)),
				title=_("Validation Errors"),
			)

		# --- Second pass: all rows are valid, add everything to child table ---
		for row in rows:
			if not row.get("evaluation_date"):
				row["evaluation_date"] = self.evaluation_import_date
			self.append("items", row)

		valid_count = len(rows)

		self.rows_parsed = valid_count

		self.computed_total_evaluations = valid_count

		self.save()

		return {"rows": valid_count}

	# ======================================================
	# CREATE TEA EVALUATION BUTTON
	# ======================================================

	@frappe.whitelist()
	def create_evaluations(self):
		created = 0

		errors = 0

		duplicates = 0

		# Dynamically fetch mandatory fields from Tea Evaluation doctype
		mandatory_fields = get_tea_evaluation_mandatory_fields()

		for row in self.items:
			if row.row_status == "Created":
				continue

			try:
				# Check all mandatory fields from Tea Evaluation doctype dynamically
				missing = []
				for fieldname in mandatory_fields:
					if not row.get(fieldname):
						# Map fieldname to a readable label
						meta = frappe.get_meta("Tea Evaluation")
						field = meta.get_field(fieldname)
						label = field.label if field else fieldname
						missing.append(label)

				if missing:
					row.row_status = "Error"
					row.message = f"Required fields missing: {', '.join(missing)}"
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

				if row.evaluation_stage and not is_valid_tea_evaluation_link_value(
					"evaluation_stage", row.evaluation_stage
				):
					row.row_status = "Error"
					row.message = f"Invalid Stage: '{row.evaluation_stage}' is not a valid option"
					errors += 1
					continue

				if row.liquor_mark and not is_valid_tea_evaluation_link_value("liquor_mark", row.liquor_mark):
					row.row_status = "Error"
					row.message = f"Invalid Liquor Mark: '{row.liquor_mark}' is not a valid option"
					errors += 1
					continue

				if row.quality_grade and not is_valid_tea_evaluation_link_value(
					"quality_grade", row.quality_grade
				):
					row.row_status = "Error"
					row.message = f"Invalid Quality Grade: '{row.quality_grade}' is not a valid option"
					errors += 1
					continue

				if row.mark and not frappe.db.exists("Mark", row.mark):
					row.row_status = "Error"
					row.message = f"Invalid Mark: '{row.mark}' not found"
					errors += 1
					continue

				if self.is_duplicate(row.tea_lot, row.taster, row.evaluation_stage, row.evaluation_date):
					row.row_status = "Duplicate"

					row.message = "Duplicate Evaluation"

					duplicates += 1

					continue

				doc = frappe.get_doc(
					{
						"doctype": "Tea Evaluation",
						"tea_lot": row.tea_lot,
						"taster": row.taster,
						"evaluation_stage": row.evaluation_stage,
						"evaluation_date": row.evaluation_date or self.evaluation_import_date,
						"liquor_mark": row.liquor_mark,
						"colour": row.colour,
						"strength": row.strength,
						"taste": row.taste,
						"briskness": row.briskness,
						"quality_grade": row.quality_grade,
						"suggested_valuation": flt(row.suggested_valuation),
						"actual_valuation": flt(row.actual_valuation),
						"notes": row.notes,
						"invoice_number": row.invoice_number,
						"mark": row.mark,
						"lot_no": row.lot_no,
						"density": row.density,
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

	def is_duplicate(self, tea_lot, taster, evaluation_stage, evaluation_date):
		if not evaluation_date:
			return False

		exists = frappe.get_all(
			"Tea Evaluation",
			filters={
				"tea_lot": tea_lot,
				"taster": taster,
				"evaluation_stage": evaluation_stage,
				"evaluation_date": getdate(evaluation_date),
			},
		)

		return bool(exists)
