# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _

from lotwise.lotwise.doctype.tea_lot.tea_lot import (
	create_tea_evaluation,
	get_evaluation_field_options,
	get_tea_lots_for_evaluation,
)


@frappe.whitelist()
def get_evaluation_lots():
	"""Fetch Tea Lots with evaluation data for the DataTable page.
	Reuses the existing get_tea_lots_for_evaluation logic from tea_lot.py
	but adds additional fields for display.
	"""
	return get_tea_lots_for_evaluation()


@frappe.whitelist()
def save_evaluation():
	"""Create a Tea Evaluation from the DataTable row data.
	Reuses the existing create_tea_evaluation logic.
	"""
	return create_tea_evaluation()


# @frappe.whitelist()
# def bulk_delete_lots():
#     """Delete selected Tea Lots.
#     Reuses the existing delete_tea_lots logic.
#     """
#     return delete_tea_lots()


@frappe.whitelist()
def get_filter_options():
	"""Fetch filter dropdown options for the page."""
	return {
		"stage_options": get_evaluation_field_options("stage"),
		"liquor_mark_options": get_evaluation_field_options("liquor_mark"),
		"quality_grade_options": get_evaluation_field_options("quality_grade"),
	}


@frappe.whitelist()
def export_evaluation_lots(filters: str | None = None) -> dict:
	"""Export Tea Lots to Excel with applied filters.

	Args:
	    filters: JSON string of filter criteria

	Returns:
	    JSON with base64 encoded Excel file and filename
	"""
	import base64
	import io

	from frappe.utils import nowdate

	# Parse filters
	filter_dict = {}
	if filters:
		filter_dict = json.loads(filters)

	# Build filter dict for direct query
	filters_dict = {}
	valid_fields = {
		"name",
		"sale_no",
		"lot_no",
		"auction_centre",
		"grade",
		"mark",
		"invoice_number",
		"status",
		"acquisition_channel",
		"purchase_status",
	}

	for field, value in filter_dict.items():
		if value and str(value).strip() and field in valid_fields:
			filters_dict[field] = ["like", "%" + str(value) + "%"]

	# Get all filtered lots directly (no pagination)
	lots = frappe.get_list(
		"Tea Lot",
		fields=["name", "sale_no", "lot_no", "auction_centre", "grade", "mark", "invoice_number"],
		filters=filters_dict if filters_dict else None,
		order_by="creation desc",
		start=0,
		page_length=2500,
	)

	if not lots:
		frappe.throw(_("No data available to export."))

	# Fetch Tea Evaluation data for all lots
	lot_names = [lot.name for lot in lots]
	evaluations = {}
	if lot_names:
		eval_list = frappe.get_list(
			"Tea Evaluation",
			fields=[
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
				"density",
				"remarks",
			],
			filters={"tea_lot": ["in", lot_names]},
		)
		for eval in eval_list:
			evaluations[eval.tea_lot] = eval

	# Prepare data for Excel
	headers = [
		"ID",
		"Lot No",
		"Sale No",
		"Invoice No",
		"Mark",
		"Grade",
		"Auction Centre",
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

	data = []
	for lot in lots:
		eval_data = evaluations.get(lot.name, {})
		row = [
			lot.get("name", ""),
			lot.get("lot_no", ""),
			lot.get("sale_no", ""),
			lot.get("invoice_number", ""),
			lot.get("mark", ""),
			lot.get("grade", ""),
			lot.get("auction_centre", ""),
			eval_data.get("taster", ""),
			eval_data.get("stage", ""),
			eval_data.get("liquor_mark", ""),
			eval_data.get("evaluation_date", ""),
			eval_data.get("suggested_valuation", ""),
			eval_data.get("colour", ""),
			eval_data.get("strength", ""),
			eval_data.get("taste", ""),
			eval_data.get("briskness", ""),
			eval_data.get("quality_grade", ""),
			eval_data.get("density", ""),
			eval_data.get("remarks", ""),
		]
		data.append(row)

	# Create Excel file using openpyxl
	from openpyxl import Workbook

	wb = Workbook()
	ws = wb.active
	ws.title = "Tea Lot Evaluation"

	# Write headers
	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	# Write data rows
	for row_idx, row_data in enumerate(data, 2):
		for col_idx, value in enumerate(row_data, 1):
			ws.cell(row=row_idx, column=col_idx, value=value)

	# Save to BytesIO
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	# Encode to base64 for safe JSON transport
	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	# Generate filename with timestamp
	timestamp = nowdate()
	filename = f"tea_lot_evaluation_{timestamp}.xlsx"

	# Return as JSON
	return {"filename": filename, "content": encoded}
