# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io
import json

import frappe
from frappe import _
from frappe.utils import flt, nowdate

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEA_LOT_FIELDS = [
	"name",
	"lot_no",
	"sale_no",
	"mark",
	"grade",
	"auction_centre",
	"invoice_number",
	"status",
]

EVALUATION_DISPLAY_FIELDS = [
	"name",
	"tea_lot",
	"invoice_number",
	"mark",
	"lot_no",
	"taster",
	"stage",
	"liquor_mark",
	"evaluation_date",
	"suggested_valuation",
	"colour",
	"strength",
	"taste",
	"briskness",
	"quality_grade",
	"density",
	"remarks",
]

ALLOWED_UPDATE_FIELDS = [
	"taster",
	"stage",
	"liquor_mark",
	"evaluation_date",
	"suggested_valuation",
	"colour",
	"strength",
	"taste",
	"briskness",
	"quality_grade",
	"density",
	"remarks",
]

TEXT_SEARCH_FIELDS = ["name", "tea_lot", "invoice_number", "mark", "lot_no", "taster"]
EXACT_MATCH_FIELDS = ["stage", "liquor_mark", "quality_grade"]

# Fields used when creating a new Tea Evaluation
CREATE_FIELDS = [
	"tea_lot",
	"taster",
	"stage",
	"liquor_mark",
	"evaluation_date",
	"suggested_valuation",
	"colour",
	"strength",
	"taste",
	"briskness",
	"quality_grade",
	"invoice_number",
	"lot_no",
	"mark",
	"density",
	"remarks",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_doctype_select_options(doctype: str, fieldname: str) -> list[str]:
	"""Extract select options from a DocType field definition."""
	try:
		field = frappe.get_meta(doctype).get_field(fieldname)
		if field and field.options:
			return [opt.strip() for opt in field.options.split("\n") if opt.strip()]
		return []
	except Exception:
		return []


def _build_filters(filter_dict: dict) -> tuple:
	"""Build Frappe filters and OR-filters from a filter dictionary."""
	frappe_filters = {}
	or_filters = []

	for field in TEXT_SEARCH_FIELDS:
		if filter_dict.get(field):
			or_filters.append([field, "like", f"%{filter_dict[field]}%"])

	for field in EXACT_MATCH_FIELDS:
		if filter_dict.get(field):
			frappe_filters[field] = filter_dict[field]

	if filter_dict.get("evaluation_date"):
		frappe_filters["evaluation_date"] = filter_dict["evaluation_date"]

	return frappe_filters, or_filters if or_filters else None


def _build_lot_filters(filter_dict: dict) -> dict:
	"""Build Tea Lot filters from a filter dictionary.

	Text fields use LIKE, select/exact-match fields use equality.
	"""
	text_search_fields = {
		"name",
		"sale_no",
		"lot_no",
		"auction_centre",
		"grade",
		"mark",
		"invoice_number",
		"acquisition_channel",
	}
	exact_match_fields = {"status", "purchase_status"}

	filters = {}
	for field, value in filter_dict.items():
		if not value or not str(value).strip():
			continue
		val = str(value).strip()
		if field in text_search_fields:
			filters[field] = ["like", "%" + val + "%"]
		elif field in exact_match_fields:
			filters[field] = val
	return filters


# ---------------------------------------------------------------------------
# Whitelisted API Methods
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_workspace_data(
	mode: str = "new",
	filters: str | None = None,
	start: int = 0,
	page_length: int = 20,
) -> dict:
	"""Fetch data for the Tea Evaluation Workspace.

	Args:
	    mode: "new" for Tea Lots without evaluations, "update" for existing evaluations.
	    filters: JSON string of filter criteria.
	    start: Pagination start offset.
	    page_length: Number of records to fetch.

	Returns:
	    dict with records, total_count, and dropdown options.
	"""
	filter_dict = json.loads(filters) if filters else {}

	# Always return dropdown options
	result = {
		"stage_options": sorted(get_doctype_select_options("Tea Evaluation", "stage")),
		"liquor_mark_options": sorted(get_doctype_select_options("Tea Evaluation", "liquor_mark")),
		"quality_grade_options": sorted(get_doctype_select_options("Tea Evaluation", "quality_grade")),
		"total_count": 0,
		"records": [],
	}

	if mode == "new":
		# Fetch Tea Lots (all lots, user can filter by status)
		lot_filters = _build_lot_filters(filter_dict)

		# Count total lots
		result["total_count"] = frappe.db.count("Tea Lot", filters=lot_filters)

		# Fetch page
		lots = frappe.get_all(
			"Tea Lot",
			fields=TEA_LOT_FIELDS,
			filters=lot_filters,
			order_by="creation desc",
			start=start,
			page_length=page_length,
		)
		result["records"] = lots

	else:  # mode == "update"
		# Fetch existing Tea Evaluations
		frappe_filters, or_filters = _build_filters(filter_dict)

		# Count
		if or_filters:
			result["total_count"] = len(
				frappe.get_list(
					"Tea Evaluation",
					filters=frappe_filters,
					or_filters=or_filters,
					fields=["name"],
					limit_start=0,
					limit_page_length=0,
				)
			)
		else:
			result["total_count"] = frappe.db.count("Tea Evaluation", filters=frappe_filters)

		# Fetch page
		evaluations = frappe.get_list(
			"Tea Evaluation",
			fields=EVALUATION_DISPLAY_FIELDS,
			filters=frappe_filters,
			or_filters=or_filters,
			order_by="evaluation_date desc, creation desc",
			start=start,
			page_length=page_length,
		)
		result["records"] = evaluations

	return result


@frappe.whitelist()
def create_evaluation() -> dict:
	"""Create a new Tea Evaluation from workspace row data."""
	data = frappe.local.form_dict

	required = ["tea_lot", "taster", "stage", "evaluation_date"]
	missing = [f for f in required if not data.get(f)]
	if missing:
		frappe.throw(_("Missing required fields: {0}").format(", ".join(missing)))

	eval_doc = frappe.get_doc(
		{
			"doctype": "Tea Evaluation",
			"tea_lot": data.get("tea_lot"),
			"taster": data.get("taster"),
			"stage": data.get("stage"),
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

	# Update Tea Lot status to Evaluated
	frappe.db.set_value("Tea Lot", data.get("tea_lot"), "status", "Evaluated")

	return {"success": True, "name": eval_doc.name, "message": _("Evaluation created successfully.")}


@frappe.whitelist()
def update_evaluation(evaluation_name: str, data: str) -> dict:
	"""Update a single Tea Evaluation record."""
	try:
		doc = frappe.get_doc("Tea Evaluation", evaluation_name)
		update_data = json.loads(data)

		for field in ALLOWED_UPDATE_FIELDS:
			if field in update_data and update_data[field] is not None and str(update_data[field]).strip():
				doc.set(field, update_data[field])

		doc.save(ignore_permissions=True)
		return {"success": True, "message": _("Evaluation updated successfully.")}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Tea Evaluation Workspace Update failed")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def bulk_save(mode: str, records: str) -> dict:
	"""Bulk save multiple evaluations (create or update)."""
	try:
		data_list = json.loads(records)
		created_count = 0
		updated_count = 0
		errors = []

		for row in data_list:
			try:
				if mode == "new":
					# Create new evaluation
					required = ["tea_lot", "taster", "stage", "evaluation_date"]
					missing = [f for f in required if not row.get(f)]
					if missing:
						errors.append(
							_("Row {0}: Missing required fields: {1}").format(
								row.get("tea_lot", "?"), ", ".join(missing)
							)
						)
						continue

					eval_doc = frappe.get_doc(
						{
							"doctype": "Tea Evaluation",
							"tea_lot": row.get("tea_lot"),
							"taster": row.get("taster"),
							"stage": row.get("stage"),
							"liquor_mark": row.get("liquor_mark"),
							"evaluation_date": row.get("evaluation_date"),
							"suggested_valuation": flt(row.get("suggested_valuation")),
							"colour": flt(row.get("colour")),
							"strength": flt(row.get("strength")),
							"taste": flt(row.get("taste")),
							"briskness": flt(row.get("briskness")),
							"quality_grade": row.get("quality_grade"),
							"invoice_number": row.get("invoice_number"),
							"lot_no": row.get("lot_no"),
							"mark": row.get("mark"),
							"density": flt(row.get("density")),
							"remarks": row.get("remarks"),
						}
					)
					eval_doc.insert()
					frappe.db.set_value("Tea Lot", row.get("tea_lot"), "status", "Evaluated")
					created_count += 1

				else:  # mode == "update"
					eval_name = row.get("name")
					if not eval_name:
						errors.append(_("Row missing evaluation name."))
						continue

					doc = frappe.get_doc("Tea Evaluation", eval_name)
					for field in ALLOWED_UPDATE_FIELDS:
						if field in row and row[field] is not None and str(row[field]).strip():
							doc.set(field, row[field])
					doc.save(ignore_permissions=True)
					updated_count += 1

			except Exception as e:
				errors.append(str(e))
				continue

		message_parts = []
		if created_count:
			message_parts.append(_("{0} evaluation(s) created.").format(created_count))
		if updated_count:
			message_parts.append(_("{0} evaluation(s) updated.").format(updated_count))
		if errors:
			message_parts.append(_("{0} error(s).").format(len(errors)))

		return {
			"success": True,
			"message": " ".join(message_parts),
			"created_count": created_count,
			"updated_count": updated_count,
			"errors": errors[:5],  # Return first 5 errors
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Tea Evaluation Workspace Bulk Save failed")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def export_data(mode: str = "new", filters: str | None = None) -> dict:
	"""Export Tea Evaluations (or lots for new evaluations) to Excel."""
	filter_dict = json.loads(filters) if filters else {}

	if mode == "new":
		# Export Tea Lots (all lots, user can filter by status)
		lot_filters = _build_lot_filters(filter_dict)
		records = frappe.get_all(
			"Tea Lot",
			fields=["name", "lot_no", "sale_no", "mark", "grade", "auction_centre", "invoice_number"],
			filters=lot_filters or None,
			order_by="creation desc",
			limit_page_length=0,
		)

		headers = ["ID", "Lot No", "Sale No", "Mark", "Grade", "Auction Centre", "Invoice No"]
		data = [
			[
				r.get("name", ""),
				r.get("lot_no", ""),
				r.get("sale_no", ""),
				r.get("mark", ""),
				r.get("grade", ""),
				r.get("auction_centre", ""),
				r.get("invoice_number", ""),
			]
			for r in records
		]

	else:  # mode == "update"
		frappe_filters, or_filters = _build_filters(filter_dict)
		evaluations = frappe.get_list(
			"Tea Evaluation",
			fields=EVALUATION_DISPLAY_FIELDS,
			filters=frappe_filters,
			or_filters=or_filters,
			order_by="evaluation_date desc, creation desc",
		)

		headers = [
			"ID",
			"Tea Lot",
			"Invoice No",
			"Mark",
			"Lot No",
			"Taster",
			"Stage",
			"Liquor Mark",
			"Eval Date",
			"Suggested Val",
			"Colour",
			"Strength",
			"Taste",
			"Briskness",
			"Quality Grade",
			"Density",
			"Remarks",
		]
		data = [
			[
				r.get("name", ""),
				r.get("tea_lot", ""),
				r.get("invoice_number", ""),
				r.get("mark", ""),
				r.get("lot_no", ""),
				r.get("taster", ""),
				r.get("stage", ""),
				r.get("liquor_mark", ""),
				r.get("evaluation_date", ""),
				r.get("suggested_valuation", ""),
				r.get("colour", ""),
				r.get("strength", ""),
				r.get("taste", ""),
				r.get("briskness", ""),
				r.get("quality_grade", ""),
				r.get("density", ""),
				r.get("remarks", ""),
			]
			for r in evaluations
		]

	if not data:
		frappe.throw(_("No data available to export."))

	from openpyxl import Workbook

	wb = Workbook()
	ws = wb.active
	ws.title = "Tea Evaluation Workspace"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, row_data in enumerate(data, 2):
		for col_idx, value in enumerate(row_data, 1):
			ws.cell(row=row_idx, column=col_idx, value=value)

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")
	filename = f"tea_evaluation_workspace_{nowdate()}.xlsx"

	return {"filename": filename, "content": encoded}
