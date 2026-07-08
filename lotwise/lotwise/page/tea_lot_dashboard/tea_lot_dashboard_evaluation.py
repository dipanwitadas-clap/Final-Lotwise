# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


@frappe.whitelist()
def get_evaluations() -> dict:
	"""
	Fetch all Tea Evaluations (client-side filtering)
	"""
	evaluations = frappe.db.sql(
		"""
		SELECT
			e.name,
			e.tea_lot,
			e.taster,
			e.stage,
			e.evaluation_date,
			e.colour,
			e.strength,
			e.taste,
			e.briskness,
			e.quality_grade,
			e.suggested_valuation,
			e.notes,
			tl.lot_no AS tea_lot_no,
			tl.mark AS tea_lot_mark
		FROM `tabTea Evaluation` e
		LEFT JOIN `tabTea Lot` tl ON tl.name = e.tea_lot
		ORDER BY e.creation DESC
		""",
		as_dict=True,
	)

	return {"evaluations": evaluations}


@frappe.whitelist()
def download_evaluation_xlsx():
	"""
	Generate .xlsx with all Tea Evaluations and return as base64
	"""
	evaluations = frappe.db.sql(
		"""
		SELECT
			e.name,
			e.tea_lot,
			e.taster,
			e.stage,
			e.evaluation_date,
			e.colour,
			e.strength,
			e.taste,
			e.briskness,
			e.quality_grade,
			e.suggested_valuation,
			e.notes,
			tl.lot_no AS tea_lot_no,
			tl.mark AS tea_lot_mark
		FROM `tabTea Evaluation` e
		LEFT JOIN `tabTea Lot` tl ON tl.name = e.tea_lot
		ORDER BY e.creation DESC
		""",
		as_dict=True,
	)

	headers = [
		"Tea Evaluation ID",
		"Tea Lot",
		"Taster",
		"Stage",
		"Evaluation Date",
		"Colour",
		"Strength",
		"Taste",
		"Briskness",
		"Quality Grade",
		"Suggested Valuation",
		"Notes",
		"Lot No",
		"Mark",
	]

	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Evaluations"

	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	for row_idx, ev in enumerate(evaluations, 2):
		ws.cell(row=row_idx, column=1, value=ev.name)
		ws.cell(row=row_idx, column=2, value=ev.tea_lot)
		ws.cell(row=row_idx, column=3, value=ev.taster)
		ws.cell(row=row_idx, column=4, value=ev.stage)
		ws.cell(row=row_idx, column=5, value=str(ev.evaluation_date) if ev.evaluation_date else None)
		ws.cell(row=row_idx, column=6, value=ev.colour)
		ws.cell(row=row_idx, column=7, value=ev.strength)
		ws.cell(row=row_idx, column=8, value=ev.taste)
		ws.cell(row=row_idx, column=9, value=ev.briskness)
		ws.cell(row=row_idx, column=10, value=ev.quality_grade)
		ws.cell(row=row_idx, column=11, value=ev.suggested_valuation)
		ws.cell(row=row_idx, column=12, value=ev.notes)
		ws.cell(row=row_idx, column=13, value=ev.tea_lot_no)
		ws.cell(row=row_idx, column=14, value=ev.tea_lot_mark)

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "tea_evaluations.xlsx"}
