# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Fields fetched from Tea Evaluation for display and export.
EVALUATION_FIELDS: list[str] = [
	"name",
	"tea_lot",
	"invoice_number",
	"mark",
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

# Fields that can be updated via the page (includes "stage" which is
# bulk-only; ``update_evaluation`` excludes it).
ALLOWED_UPDATE_FIELDS: list[str] = [
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

# Fields that are excluded from single-row updates (bulk-only).
SINGLE_ROW_EXCLUDED_FIELDS: list[str] = ["stage"]

# Filter configuration: text-search fields use ``like``, exact-match fields
# use equality, and the date field is matched exactly.
TEXT_SEARCH_FIELDS: list[str] = ["name", "tea_lot", "invoice_number", "mark", "taster"]
EXACT_MATCH_FIELDS: list[str] = ["stage", "liquor_mark", "quality_grade"]


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


def _build_filters(filter_dict: dict[str, Any]) -> tuple[dict[str, Any], list[list[Any]] | None]:
	"""Build Frappe filters and OR-filters from a filter dictionary.

	Returns a tuple of ``(frappe_filters, or_filters)`` where ``or_filters``
	is ``None`` when no text-search filters are present.
	"""
	frappe_filters: dict[str, Any] = {}
	or_filters: list[list[Any]] = []

	for field in TEXT_SEARCH_FIELDS:
		if filter_dict.get(field):
			or_filters.append([field, "like", f"%{filter_dict[field]}%"])

	for field in EXACT_MATCH_FIELDS:
		if filter_dict.get(field):
			frappe_filters[field] = filter_dict[field]

	if filter_dict.get("evaluation_date"):
		frappe_filters["evaluation_date"] = filter_dict["evaluation_date"]

	return frappe_filters, or_filters if or_filters else None


def _parse_filters(filters: str | None) -> dict[str, Any]:
	"""Parse a JSON filter string into a dictionary (empty dict if falsy)."""
	if filters:
		return json.loads(filters)
	return {}


def _get_evaluation_dropdown_options() -> dict[str, list[str]]:
	"""Fetch dropdown options for stage, liquor_mark, and quality_grade."""
	return {
		"stage_options": sorted(get_doctype_select_options("Tea Evaluation", "stage")),
		"liquor_mark_options": sorted(get_doctype_select_options("Tea Evaluation", "liquor_mark")),
		"quality_grade_options": sorted(get_doctype_select_options("Tea Evaluation", "quality_grade")),
	}


def _count_evaluations(frappe_filters: dict[str, Any], or_filters: list[list[Any]] | None) -> int:
	"""Count Tea Evaluation records efficiently.

	Uses ``frappe.db.count`` when there are no OR-filters (fast path).
	Falls back to ``frappe.get_list`` with no limit when OR-filters exist,
	since ``frappe.db.count`` does not support ``or_filters``.
	"""
	if or_filters:
		return len(
			frappe.get_list(
				"Tea Evaluation",
				filters=frappe_filters,
				or_filters=or_filters,
				fields=["name"],
				limit_start=0,
				limit_page_length=0,
			)
		)
	return frappe.db.count("Tea Evaluation", filters=frappe_filters)


# ---------------------------------------------------------------------------
# Whitelisted API methods
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_evaluations(filters: str | None = None, start: int = 0, page_length: int = 20) -> dict[str, Any]:
	"""Fetch Tea Evaluation records with applied filters and pagination."""
	filter_dict = _parse_filters(filters)
	frappe_filters, or_filters = _build_filters(filter_dict)

	total_count = _count_evaluations(frappe_filters, or_filters)

	evaluations = frappe.get_list(
		"Tea Evaluation",
		fields=EVALUATION_FIELDS,
		filters=frappe_filters,
		or_filters=or_filters,
		order_by="evaluation_date desc, creation desc",
		start=start,
		page_length=page_length,
	)

	return {
		"evaluations": evaluations,
		"total_count": total_count,
		**_get_evaluation_dropdown_options(),
	}


@frappe.whitelist()
def update_evaluation(evaluation_name: str, data: str) -> dict[str, Any]:
	"""Update a single Tea Evaluation record."""
	try:
		doc = frappe.get_doc("Tea Evaluation", evaluation_name)
		update_data = json.loads(data)

		allowed_fields = [f for f in ALLOWED_UPDATE_FIELDS if f not in SINGLE_ROW_EXCLUDED_FIELDS]

		for field in allowed_fields:
			if field in update_data and update_data[field] is not None and str(update_data[field]).strip():
				doc.set(field, update_data[field])

		doc.save(ignore_permissions=True)
		return {"success": True, "message": _("Evaluation updated successfully.")}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Tea Evaluation Update failed")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def bulk_update_evaluations(evaluation_names: str, data: str) -> dict[str, Any]:
	"""Bulk update multiple Tea Evaluation records."""
	try:
		names = json.loads(evaluation_names)
		update_data = json.loads(data)

		updated_count = 0
		for name in names:
			try:
				doc = frappe.get_doc("Tea Evaluation", name)
				row_updates = update_data.get(name, {})
				for field in ALLOWED_UPDATE_FIELDS:
					if (
						field in row_updates
						and row_updates[field] is not None
						and str(row_updates[field]).strip()
					):
						doc.set(field, row_updates[field])
				doc.save(ignore_permissions=True)
				updated_count += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Bulk update failed for {name}")
				continue

		return {
			"success": True,
			"message": _("{0} evaluation(s) updated successfully.").format(updated_count),
			"updated_count": updated_count,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Bulk Tea Evaluation Update failed")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def export_evaluations(filters: str | None = None) -> dict[str, Any]:
	"""Export Tea Evaluations to Excel with applied filters."""
	filter_dict = _parse_filters(filters)
	frappe_filters, or_filters = _build_filters(filter_dict)

	evaluations = frappe.get_list(
		"Tea Evaluation",
		fields=EVALUATION_FIELDS,
		filters=frappe_filters,
		or_filters=or_filters,
		order_by="evaluation_date desc, creation desc",
	)

	if not evaluations:
		frappe.throw(_("No data available to export."))

	# Prepare data for Excel
	headers = [
		"ID",
		"Tea Lot",
		"Invoice No",
		"Mark",
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
			eval.get("name", ""),
			eval.get("tea_lot", ""),
			eval.get("invoice_number", ""),
			eval.get("mark", ""),
			eval.get("taster", ""),
			eval.get("stage", ""),
			eval.get("liquor_mark", ""),
			eval.get("evaluation_date", ""),
			eval.get("suggested_valuation", ""),
			eval.get("colour", ""),
			eval.get("strength", ""),
			eval.get("taste", ""),
			eval.get("briskness", ""),
			eval.get("quality_grade", ""),
			eval.get("density", ""),
			eval.get("remarks", ""),
		]
		for eval in evaluations
	]

	# Create Excel file using openpyxl
	from openpyxl import Workbook

	wb = Workbook()
	ws = wb.active
	ws.title = "Tea Evaluation"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, row_data in enumerate(data, 2):
		for col_idx, value in enumerate(row_data, 1):
			ws.cell(row=row_idx, column=col_idx, value=value)

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")
	filename = f"tea_evaluation_{nowdate()}.xlsx"

	return {"filename": filename, "content": encoded}
