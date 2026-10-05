# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, getdate
from openpyxl.utils import get_column_letter


class TeaLot(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.tea_lot_reprint.tea_lot_reprint import TeaLotReprint

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		awr_date: DF.Date | None
		blend: DF.Link | None
		broker: DF.Link | None
		certification: DF.Data | None
		chest_serial_range: DF.Data | None
		density: DF.Float
		division: DF.Data | None
		do_date: DF.Data | None
		do_reference: DF.Data | None
		evaluation_status: DF.Link | None
		fiscal_year: DF.Link | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		grade: DF.Link | None
		gross_wtpkg: DF.Float
		intended_segment: DF.Link | None
		invoice_number: DF.Data | None
		item: DF.Link | None
		liquor_mark: DF.Link | None
		lot_no: DF.Data | None
		manufacturer_ref: DF.Data | None
		mark: DF.Link
		mfg_monthyear: DF.Data | None
		net_weight_total: DF.Float
		net_wtpkg: DF.Float
		offer_check: DF.Check
		offer_date: DF.Date | None
		offer_sample_list: DF.Link | None
		packages: DF.Int
		packing: DF.Link | None
		purchase_check: DF.Check
		purchase_date: DF.Date | None
		purchase_from: DF.Data | None
		purchase_invoice_date: DF.Date | None
		purchase_invoice_no: DF.Data | None
		purchase_status: DF.Link | None
		rate: DF.Currency
		reprints: DF.Table[TeaLotReprint]
		sale_no: DF.Int
		season: DF.Int
		seller: DF.Link | None
		source_doctype: DF.Link | None
		source_doctype_id: DF.DynamicLink | None
		suggested_valuation: DF.Currency
		tea_purchase: DF.Link | None
		total_amount_as_per_to_tax_invoice: DF.Float
		warehouse: DF.Link | None
		warehouse_name: DF.Data | None
		warehouselocation: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.validate_fiscal_year()
		self.set_status_checks()

	def set_status_checks(self):
		if self.purchase_status == "Offer":
			self.offer_check = 1
		if self.purchase_status == "Purchase":
			self.purchase_check = 1

	def validate_fiscal_year(self):
		if not self.fiscal_year:
			return

		if self.purchase_status == "Offer":
			relevant_date = self.offer_date
			date_label = _("Offer Date")
		else:
			relevant_date = self.purchase_date
			date_label = _("Purchase Date")

		if not relevant_date:
			return

		year_start_date, year_end_date = frappe.db.get_value(
			"Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"]
		)
		relevant_date = getdate(relevant_date)

		if relevant_date < year_start_date or relevant_date > year_end_date:
			frappe.throw(
				_(
					"{0} <b>{1}</b> must fall within Fiscal Year <b>{2}</b> (<b>{3}</b> to <b>{4}</b>)."
				).format(
					date_label,
					frappe.utils.formatdate(relevant_date, "dd-MMM-yyyy"),
					self.fiscal_year,
					frappe.utils.formatdate(year_start_date, "dd-MMM-yyyy"),
					frappe.utils.formatdate(year_end_date, "dd-MMM-yyyy"),
				),
				title=_("Invalid {0}").format(date_label),
			)

	def autoname(self):
		if self.acquisition_channel in ["Auction", "Outsourced"]:
			centre_code = frappe.db.get_value(
				"Auction Centre",
				self.auction_centre,
				"auction_centre_code",
			)

			if not centre_code:
				frappe.throw(_("Auction Centre Code not found."))

			if not self.season:
				frappe.throw(_("Season is required to generate the Tea Lot name."))

			if not self.sale_no:
				frappe.throw(_("Sale No is required to generate the Tea Lot name."))

			if not self.lot_no:
				frappe.throw(_("Lot No is required to generate the Tea Lot name."))

			self.name = f"{centre_code}-{self.season}-{self.sale_no}-{self.lot_no}"

		elif self.acquisition_channel == "Private":
			if not self.invoice_number:
				frappe.throw(_("Garden Invoice No. is required."))

			if not self.mark:
				frappe.throw(_("Garden Name (Mark) is required."))

			if not self.grade:
				frappe.throw(_("Grade is required."))

			if (
				self.purchase_status != "Offer"
				and not self.offer_sample_list
				and not self.purchase_invoice_no
			):
				frappe.throw(_("purchase_invoice_no is required."))

			if self.purchase_status == "Offer":
				year = getdate(self.offer_date).strftime("%y")
			else:
				year = getdate(self.purchase_date).strftime("%y")

			if self.purchase_status != "Offer" and not self.offer_sample_list:
				purchase_invoice = str(self.purchase_invoice_no)

				if "-" in purchase_invoice:
					first, second = purchase_invoice.rsplit("-", 1)
					last_part = f"{first[-1]}-{second}"
				else:
					last_part = purchase_invoice

				self.name = f"{self.invoice_number}-{year}-{self.mark}-{self.grade}-{last_part}"
			else:
				self.name = f"{self.invoice_number}-{year}-{self.mark}-{self.grade}"

		else:
			self.name = make_autoname("LOT-.####")

	# def autoname(self):
	# 	if self.acquisition_channel == "Auction":
	# 		centre_code = frappe.db.get_value(
	# 			"Auction Centre",
	# 			self.auction_centre,
	# 			"auction_centre_code",
	# 		)

	# 		if not centre_code:
	# 			frappe.throw(_("Auction Centre Code not found."))

	# 		if not self.purchase_date:
	# 			frappe.throw(_("Purchase Date is required to generate the Tea Lot name."))

	# 		if not self.lot_no:
	# 			frappe.throw(_("Lot No is required to generate the Tea Lot name."))

	# 		if not self.sale_no:
	# 			frappe.throw(_("Sale No is required to generate the Tea Lot name."))

	# 		year = getdate(self.purchase_date).strftime("%y")
	# 		self.name = f"{centre_code}-{self.lot_no}-{self.sale_no}-{year}"

	# 	elif self.acquisition_channel == "Private":
	# 		if not self.invoice_number:
	# 			frappe.throw(_("Garden Invoice No. is required."))

	# 		if not self.purchase_date:
	# 			frappe.throw(_("Purchase Date is required."))

	# 		if not self.mark:
	# 			frappe.throw(_("Garden Name (Mark) is required."))

	# 		if not self.grade:
	# 			frappe.throw(_("Grade is required."))

	# 		if not self.purchase_invoice_no:
	# 			frappe.throw(_("Tax Invoice No. is required."))

	# 		year = getdate(self.purchase_date).strftime("%y")
	# 		last_part = str(self.purchase_invoice_no)[-5:]

	# 		self.name = f"{self.invoice_number}/{year}/{self.mark}/{self.grade}/{last_part}"

	# def autoname(self):
	# 	centre_code = frappe.db.get_value(
	# 		"Auction Centre",
	# 		self.auction_centre,
	# 		"auction_centre_code",
	# 	)

	# 	if not centre_code:
	# 		frappe.throw(_("Auction Centre Code not found."))

	# 	if not self.purchase_date:
	# 		frappe.throw(_("Purchase Date is required to generate the Tea Lot name."))

	# 	if not self.lot_no:
	# 		frappe.throw(_("Lot No is required to generate the Tea Lot name."))

	# 	if not self.sale_no:
	# 		frappe.throw(_("Sale No is required to generate the Tea Lot name."))

	# 	year = getdate(self.purchase_date).strftime("%y")

	# 	self.name = f"{centre_code}-{self.lot_no}-{self.sale_no}-{year}"


# ============================================================
# HELPERS
# ============================================================


def get_evaluation_field_options(fieldname: str) -> list:
	"""Fetch options from the linked doctype for evaluation fields."""
	doctype_map = {
		"evaluation_stage": "Evaluation Stage",
		"liquor_mark": "Liquor Mark",
		"quality_grade": "Quality Grade",
	}
	doctype = doctype_map.get(fieldname)
	if not doctype:
		return []

	# Fetch all records from the linked doctype
	records = frappe.get_all(doctype, pluck="name", order_by="creation asc")
	return records or []


# ============================================================
# API: GET TEA LOTS FOR EVALUATION DATATABLE
# ============================================================


@frappe.whitelist()
def get_tea_lots_for_evaluation() -> dict:
	"""Fetch Tea Lots with their data for the inline evaluation DataTable."""
	filters_json = frappe.form_dict.get("filters")
	filters_dict = {}
	valid_fields = {
		"name",
		"sale_no",
		"lot_no",
		"auction_centre",
		"grade",
		"mark",
		"invoice_number",
		"evaluation_status",
		"acquisition_channel",
		"purchase_status",
	}

	if filters_json:
		try:
			import json

			filters = json.loads(filters_json)
			for field, value in filters.items():
				if value and str(value).strip() and field in valid_fields:
					filters_dict[field] = ["like", "%" + str(value) + "%"]
		except Exception:
			pass

	# Get pagination parameters
	start = int(frappe.form_dict.get("start", 0))
	page_length = int(frappe.form_dict.get("page_length", 20))

	# Get total count for pagination
	total_count = frappe.db.count("Tea Lot", filters=filters_dict if filters_dict else None)

	# Fetch paginated data
	lots = frappe.get_list(
		"Tea Lot",
		fields=["name", "sale_no", "lot_no", "auction_centre", "grade", "mark", "invoice_number"],
		filters=filters_dict if filters_dict else None,
		order_by="creation desc",
		start=start,
		page_length=page_length,
	)

	# Fetch dropdown options for evaluation fields
	stage_options = get_evaluation_field_options("evaluation_stage")
	liquor_mark_options = get_evaluation_field_options("liquor_mark")
	quality_grade_options = get_evaluation_field_options("quality_grade")

	return {
		"lots": lots,
		"stage_options": stage_options,
		"liquor_mark_options": liquor_mark_options,
		"quality_grade_options": quality_grade_options,
		"total_count": total_count,
		"start": start,
		"page_length": page_length,
	}


# ============================================================
# API: CREATE TEA EVALUATION (from inline DataTable)
# ============================================================


@frappe.whitelist()
def create_tea_evaluation() -> dict:
	"""
	Create a Tea Evaluation from the inline DataTable row data.
	Expects POST data via frappe.call with args:
		tea_lot, taster, evaluation_stage, liquor_mark, evaluation_date,
		suggested_valuation, colour, strength, taste, briskness,
		quality_grade, invoice_number, mark, notes
	"""
	data = frappe.local.form_dict

	required = ["tea_lot", "taster", "evaluation_stage", "evaluation_date"]
	missing = [f for f in required if not data.get(f)]
	if missing:
		frappe.throw(_("Missing required fields: {0}").format(", ".join(missing)))

	eval_doc = frappe.get_doc(
		{
			"doctype": "Tea Evaluation",
			"tea_lot": data.get("tea_lot"),
			"taster": data.get("taster"),
			"evaluation_stage": data.get("evaluation_stage"),
			"liquor_mark": data.get("liquor_mark"),
			"evaluation_date": data.get("evaluation_date"),
			"suggested_valuation": flt(data.get("suggested_valuation")),
			"colour": flt(data.get("colour")),
			"strength": flt(data.get("strength")),
			"taste": flt(data.get("taste")),
			"briskness": flt(data.get("briskness")),
			"quality_grade": data.get("quality_grade"),
			"invoice_number": data.get("invoice_number"),
			"lot_no": data.get("lot_no"),
			"mark": data.get("mark"),
			"density": flt(data.get("density")),
			"remarks": data.get("remarks"),
		}
	)

	eval_doc.insert()

	return {"name": eval_doc.name, "tea_lot": eval_doc.tea_lot}


# ============================================================
# XLSX DOWNLOAD - EVALUATION IMPORT
# ============================================================


@frappe.whitelist()
def download_evaluation_import_xlsx() -> dict:
	"""Generate xlsx for Tea Lot evaluation import with dropdown validations."""
	# Fetch unevaluated Tea Lots, including reference fields for context
	lots = frappe.db.sql(
		"""
		SELECT name, mark, invoice_number, lot_no, purchase_status, grade, density,
			liquor_mark, purchase_date, evaluation_status, sale_no, auction_centre
		FROM `tabTea Lot`
		WHERE evaluation_status != "Evaluated" OR evaluation_status IS NULL
		ORDER BY creation DESC
		""",
		as_dict=True,
	)

	# Fetch dropdown options dynamically from linked doctypes
	stage_options = get_evaluation_field_options("evaluation_stage")
	liquor_mark_options = get_evaluation_field_options("liquor_mark")
	quality_grade_options = get_evaluation_field_options("quality_grade")
	taster_options = frappe.get_all("Taster", pluck="name", order_by="creation asc")

	# Create workbook
	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Evaluations"

	# ============================================================
	# Headers
	# ============================================================
	# Reference columns (pre-filled from Tea Lot) followed by the
	# evaluation input columns (left blank for the taster to fill in).
	headers = [
		"Tea Lot",
		"Lot No",
		"Sale No",
		"Mark",
		"Grade",
		"Invoice Number",
		"Auction Centre",
		"Purchase Status",
		"Density",
		"Liquor Mark (Tea Lot)",
		"Purchase Date (DD-MM-YYYY)",
		"Evaluation Status",
		"Taster",
		"Stage",
		"Liquor Mark",
		"Colour",
		"Strength",
		"Taste",
		"Briskness",
		"Quality Grade",
		"Suggested Valuation",
		"Notes",
		"Evaluation Date (DD-MM-YYYY)",
	]
	col = {header: idx for idx, header in enumerate(headers, 1)}

	# Write headers
	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	# Write data rows (Tea Lot reference columns filled; evaluation input columns left blank)
	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=col["Tea Lot"], value=lot.name)
		ws.cell(row=row_idx, column=col["Mark"], value=lot.mark)
		ws.cell(row=row_idx, column=col["Invoice Number"], value=lot.invoice_number)
		ws.cell(row=row_idx, column=col["Lot No"], value=lot.lot_no)
		ws.cell(row=row_idx, column=col["Purchase Status"], value=lot.purchase_status)
		ws.cell(row=row_idx, column=col["Grade"], value=lot.grade)
		ws.cell(row=row_idx, column=col["Density"], value=lot.density)
		ws.cell(row=row_idx, column=col["Liquor Mark (Tea Lot)"], value=lot.liquor_mark)
		ws.cell(
			row=row_idx,
			column=col["Purchase Date (DD-MM-YYYY)"],
			value=lot.purchase_date.strftime("%d-%m-%Y") if lot.purchase_date else None,
		)
		ws.cell(row=row_idx, column=col["Evaluation Status"], value=lot.evaluation_status)
		ws.cell(row=row_idx, column=col["Sale No"], value=lot.sale_no)
		ws.cell(row=row_idx, column=col["Auction Centre"], value=lot.auction_centre)
		# Remaining evaluation-input columns remain blank (already None by default)

	# ============================================================
	# Write dropdown options in hidden columns, placed well after
	# the last real header column so they never collide with data
	# ============================================================
	options_start_col = len(headers) + 2
	stage_col = get_column_letter(options_start_col)
	liquor_col = get_column_letter(options_start_col + 1)
	grade_col = get_column_letter(options_start_col + 2)
	taster_col = get_column_letter(options_start_col + 3)

	# Stage options starting from row 2
	for idx, opt in enumerate(stage_options, 2):
		ws.cell(row=idx, column=options_start_col, value=opt)
	stage_last_row = max(len(stage_options) + 1, 2)

	# Liquor Mark options starting from row 2
	for idx, opt in enumerate(liquor_mark_options, 2):
		ws.cell(row=idx, column=options_start_col + 1, value=opt)
	liquor_last_row = max(len(liquor_mark_options) + 1, 2)

	# Quality Grade options starting from row 2
	for idx, opt in enumerate(quality_grade_options, 2):
		ws.cell(row=idx, column=options_start_col + 2, value=opt)
	grade_last_row = max(len(quality_grade_options) + 1, 2)

	# Taster options starting from row 2
	for idx, opt in enumerate(taster_options, 2):
		ws.cell(row=idx, column=options_start_col + 3, value=opt)
	taster_last_row = max(len(taster_options) + 1, 2)

	# Hide the options columns so users don't see the raw dropdown data
	ws.column_dimensions[stage_col].hidden = True
	ws.column_dimensions[liquor_col].hidden = True
	ws.column_dimensions[grade_col].hidden = True
	ws.column_dimensions[taster_col].hidden = True

	# ============================================================
	# Add Data Validation (Dropdown) using same-sheet references
	# ============================================================

	last_data_row = len(lots) + 1  # +1 for header row
	if last_data_row < 2:
		last_data_row = 2  # at least cover row 2 even if no data

	# Stage input column
	if stage_options:
		stage_range = f"${stage_col}$2:${stage_col}${stage_last_row}"
		stage_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=stage_range,
			allow_blank=True,
		)
		stage_dv.error = "Please select a valid Stage value from the dropdown."
		stage_dv.errorTitle = "Invalid Stage"
		stage_dv.prompt = "Select Stage from the list"
		stage_dv.promptTitle = "Stage"
		ws.add_data_validation(stage_dv)
		stage_input_col = get_column_letter(col["Stage"])
		stage_dv.add(f"{stage_input_col}2:{stage_input_col}{last_data_row}")

	# Liquor Mark input column
	if liquor_mark_options:
		liquor_range = f"${liquor_col}$2:${liquor_col}${liquor_last_row}"
		liquor_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=liquor_range,
			allow_blank=True,
		)
		liquor_dv.error = "Please select a valid Liquor Mark value from the dropdown."
		liquor_dv.errorTitle = "Invalid Liquor Mark"
		liquor_dv.prompt = "Select Liquor Mark from the list"
		liquor_dv.promptTitle = "Liquor Mark"
		ws.add_data_validation(liquor_dv)
		liquor_input_col = get_column_letter(col["Liquor Mark"])
		liquor_dv.add(f"{liquor_input_col}2:{liquor_input_col}{last_data_row}")

	# Quality Grade input column
	if quality_grade_options:
		grade_range = f"${grade_col}$2:${grade_col}${grade_last_row}"
		grade_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=grade_range,
			allow_blank=True,
		)
		grade_dv.error = "Please select a valid Quality Grade value from the dropdown."
		grade_dv.errorTitle = "Invalid Quality Grade"
		grade_dv.prompt = "Select Quality Grade from the list"
		grade_dv.promptTitle = "Quality Grade"
		ws.add_data_validation(grade_dv)
		grade_input_col = get_column_letter(col["Quality Grade"])
		grade_dv.add(f"{grade_input_col}2:{grade_input_col}{last_data_row}")

	# Taster input column
	if taster_options:
		taster_range = f"${taster_col}$2:${taster_col}${taster_last_row}"
		taster_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=taster_range,
			allow_blank=True,
		)
		taster_dv.error = "Please select a valid Taster value from the dropdown."
		taster_dv.errorTitle = "Invalid Taster"
		taster_dv.prompt = "Select Taster from the list"
		taster_dv.promptTitle = "Taster"
		ws.add_data_validation(taster_dv)
		taster_input_col = get_column_letter(col["Taster"])
		taster_dv.add(f"{taster_input_col}2:{taster_input_col}{last_data_row}")

	# Save to BytesIO
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	# Encode to base64 for safe JSON transport
	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "tea_evaluation_import.xlsx"}


# ============================================================
# API: BULK DELETE TEA LOTS
# ============================================================


# @frappe.whitelist()
# def delete_tea_lots():
# 	"""Delete multiple Tea Lots quickly using direct SQL.

# 	Uses fast bulk SQL deletion instead of frappe.delete_doc
# 	to avoid expensive hooks/validations per document.
# 	Also deletes linked Tea Evaluations first.
# 	"""
# 	import json

# 	names = frappe.form_dict.get("names")
# 	if isinstance(names, str):
# 		names = json.loads(names)

# 	if not names or not isinstance(names, list):
# 		frappe.throw(_("No Tea Lots selected for deletion."))

# 	if not frappe.has_permission("Tea Lot", "delete"):
# 		frappe.throw(_("Not permitted to delete Tea Lots."))

# 	# Build parameterized placeholders for SQL IN clause
# 	placeholders = ", ".join(["%s"] * len(names))

# 	# 1. First delete any Tea Evaluations linked to these Tea Lots
# 	frappe.db.sql(
# 		f"DELETE FROM `tabTea Evaluation` WHERE tea_lot IN ({placeholders})",
# 		names,
# 	)

# 	# 2. Then delete the Tea Lots themselves (fast SQL, no hooks/validations)
# 	frappe.db.sql(
# 		f"DELETE FROM `tabTea Lot` WHERE name IN ({placeholders})",
# 		names,
# 	)

# 	frappe.db.commit()

# 	# Clear cache for deleted documents
# 	for name in names:
# 		frappe.clear_document_cache("Tea Lot", name)

# 	return {"deleted_count": len(names), "deleted": names}
