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
	"evaluation_status",
]

TEXT_SEARCH_FIELDS = ["name", "tea_lot", "invoice_number", "mark", "lot_no", "taster"]
EXACT_MATCH_FIELDS = ["evaluation_stage", "liquor_mark", "quality_grade"]

CREATE_FIELDS = [
	"tea_lot",
	"taster",
	"evaluation_stage",
	"liquor_mark",
	"evaluation_date",
	"suggested_valuation",
	"actual_valuation",
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
	"""Fetch options from the linked doctype for evaluation fields."""
	doctype_map = {
		"evaluation_stage": "Evaluation Stage",
		"liquor_mark": "Liquor Mark",
		"quality_grade": "Quality Grade",
	}
	linked_doctype = doctype_map.get(fieldname)
	if not linked_doctype:
		return []
	try:
		records = frappe.get_all(linked_doctype, pluck="name", order_by="creation asc")
		return records or []
	except Exception:
		return []


def _build_lot_filters(filter_dict: dict) -> dict:
	"""Build Tea Lot filters from a filter dictionary.

	Text fields use LIKE, select/exact-match fields use equality.
	Note: 'tea_lot' is handled by mapping to 'name' since we query Tea Lots directly.
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
	exact_match_fields = {"evaluation_status", "purchase_status"}

	filters = {}
	for field, value in filter_dict.items():
		if not value or not str(value).strip():
			continue
		val = str(value).strip()
		# Map 'tea_lot' to 'name' for Tea Lot queries
		if field == "tea_lot":
			field = "name"
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
	filters: str | None = None,
	start: int = 0,
	page_length: int = 20,
	sort_order: str = "desc",
) -> dict:
	"""Fetch data for the Tea Evaluation Entry page.

	Args:
	    filters: JSON string of filter criteria.
	    start: Pagination start offset.
	    page_length: Number of records to fetch.
	    sort_order: "asc" or "desc" order for the record listing.

	Returns:
	    dict with records, total_count, and dropdown options.
	"""
	sort_order = "asc" if sort_order == "asc" else "desc"
	filter_dict = json.loads(filters) if filters else {}

	# Check if logged-in user is linked to a Taster record
	default_taster = frappe.db.get_value("Taster", {"user": frappe.session.user}, "name")

	# Always return dropdown options
	result = {
		"stage_options": sorted(get_doctype_select_options("Tea Evaluation", "evaluation_stage")),
		"liquor_mark_options": sorted(get_doctype_select_options("Tea Evaluation", "liquor_mark")),
		"quality_grade_options": sorted(get_doctype_select_options("Tea Evaluation", "quality_grade")),
		"total_count": 0,
		"records": [],
		"default_taster": default_taster or "",
	}

	# Fetch Tea Lots (all lots, user can filter by status)
	lot_filters = _build_lot_filters(filter_dict)

	# Count total lots
	result["total_count"] = frappe.db.count("Tea Lot", filters=lot_filters)

	# Fetch page
	lots = frappe.get_all(
		"Tea Lot",
		fields=TEA_LOT_FIELDS,
		filters=lot_filters,
		order_by=f"creation {sort_order}",
		start=start,
		page_length=page_length,
	)
	result["records"] = lots

	return result


@frappe.whitelist()
def create_evaluation() -> dict:
	"""Create a new Tea Evaluation from workspace row data."""
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
			"actual_valuation": flt(data.get("actual_valuation")),
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

	# Update Tea Lot evaluation_status to Evaluated
	frappe.db.set_value("Tea Lot", data.get("tea_lot"), "evaluation_status", "Evaluated")

	return {"success": True, "name": eval_doc.name, "message": _("Evaluation created successfully.")}


@frappe.whitelist()
def bulk_save(records: str) -> dict:
	"""Bulk save multiple evaluations (create only)."""
	try:
		data_list = json.loads(records)
		created_count = 0
		errors = []

		for row in data_list:
			try:
				# Create new evaluation
				required = ["tea_lot", "taster", "evaluation_stage", "evaluation_date"]
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
						"evaluation_stage": row.get("evaluation_stage"),
						"liquor_mark": row.get("liquor_mark"),
						"evaluation_date": row.get("evaluation_date"),
						"suggested_valuation": flt(row.get("suggested_valuation")),
						"actual_valuation": flt(row.get("actual_valuation")),
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
				frappe.db.set_value("Tea Lot", row.get("tea_lot"), "evaluation_status", "Evaluated")
				created_count += 1

			except Exception as e:
				errors.append(str(e))
				continue

		message_parts = []
		if created_count:
			message_parts.append(_("{0} evaluation(s) created.").format(created_count))
		if errors:
			message_parts.append(_("{0} error(s).").format(len(errors)))

		return {
			"success": True,
			"message": " ".join(message_parts),
			"created_count": created_count,
			"errors": errors[:5],  # Return first 5 errors
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Tea Evaluation Entry Bulk Save failed")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def export_data(filters: str | None = None, table_data: str | None = None) -> dict:
	"""Export Tea Lots with evaluation fields to Excel for new evaluations."""
	try:
		headers = [
			"ID",
			"Lot No",
			"Sale No",
			"Mark",
			"Grade",
			"Auction Centre",
			"Invoice No",
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
			"Actual Val",
		]

		from openpyxl import Workbook

		wb = Workbook()
		ws = wb.active
		ws.title = "Tea Evaluation Entry"

		# Write headers
		for col_idx, header in enumerate(headers, 1):
			ws.cell(row=1, column=col_idx, value=header)

		row_idx = 2

		# If table_data is provided from frontend, use it
		if table_data:
			data_list = json.loads(table_data)
			for r in data_list:
				ws.cell(row=row_idx, column=1, value=r.get("name", ""))
				ws.cell(row=row_idx, column=2, value=r.get("lot_no", ""))
				ws.cell(row=row_idx, column=3, value=r.get("sale_no", ""))
				ws.cell(row=row_idx, column=4, value=r.get("mark", ""))
				ws.cell(row=row_idx, column=5, value=r.get("grade", ""))
				ws.cell(row=row_idx, column=6, value=r.get("auction_centre", ""))
				ws.cell(row=row_idx, column=7, value=r.get("invoice_number", ""))
				ws.cell(row=row_idx, column=8, value=r.get("taster", ""))
				ws.cell(row=row_idx, column=9, value=r.get("stage", ""))
				ws.cell(row=row_idx, column=10, value=r.get("liquor_mark", ""))
				ws.cell(row=row_idx, column=11, value=r.get("evaluation_date", ""))
				ws.cell(row=row_idx, column=12, value=r.get("suggested_valuation", ""))
				ws.cell(row=row_idx, column=13, value=r.get("colour", ""))
				ws.cell(row=row_idx, column=14, value=r.get("strength", ""))
				ws.cell(row=row_idx, column=15, value=r.get("taste", ""))
				ws.cell(row=row_idx, column=16, value=r.get("briskness", ""))
				ws.cell(row=row_idx, column=17, value=r.get("quality_grade", ""))
				ws.cell(row=row_idx, column=18, value=r.get("density", ""))
				ws.cell(row=row_idx, column=19, value=r.get("remarks", ""))
				ws.cell(row=row_idx, column=20, value=r.get("actual_valuation", ""))
				row_idx += 1
		else:
			# Fallback: fetch from database
			filter_dict = json.loads(filters) if filters else {}
			lot_filters = _build_lot_filters(filter_dict)
			if not lot_filters:
				lot_filters = None

			records = frappe.get_all(
				"Tea Lot",
				fields=[
					"name",
					"lot_no",
					"sale_no",
					"mark",
					"grade",
					"auction_centre",
					"invoice_number",
				],
				filters=lot_filters,
				order_by="creation desc",
				limit_page_length=0,
			)

			if not records:
				frappe.throw(_("No data available to export."))

			for r in records:
				ws.cell(row=row_idx, column=1, value=r.get("name", ""))
				ws.cell(row=row_idx, column=2, value=r.get("lot_no", ""))
				ws.cell(row=row_idx, column=3, value=r.get("sale_no", ""))
				ws.cell(row=row_idx, column=4, value=r.get("mark", ""))
				ws.cell(row=row_idx, column=5, value=r.get("grade", ""))
				ws.cell(row=row_idx, column=6, value=r.get("auction_centre", ""))
				ws.cell(row=row_idx, column=7, value=r.get("invoice_number", ""))
				# Columns 8-20 left empty for evaluation fields
				row_idx += 1

		output = io.BytesIO()
		wb.save(output)
		output.seek(0)

		encoded = base64.b64encode(output.getvalue()).decode("utf-8")
		filename = f"tea_evaluation_entry_{nowdate()}.xlsx"

		return {"filename": filename, "content": encoded}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Tea Evaluation Entry Export failed")
		frappe.throw(_("Export failed: {0}").format(str(e)))
