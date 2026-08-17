# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _

NUMERIC_SCORE_FIELDS = ["colour", "strength", "taste", "briskness"]


def execute(filters=None):
	filters = filters or {}

	stage_1 = filters.get("stage_1") or ""
	stage_2 = filters.get("stage_2") or ""

	columns = get_columns(stage_1, stage_2)
	data = get_data(filters, stage_1, stage_2)
	summary = get_report_summary(data, stage_1, stage_2)

	# Skip Frappe's automatic total row since a comparison summary is added separately
	return columns, data, None, None, summary, 1


def get_columns(stage_1, stage_2):
	columns = [
		{
			"label": _("Tea Lot"),
			"fieldname": "tea_lot",
			"fieldtype": "Link",
			"options": "Tea Lot",
			"width": 130,
		},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 100},
		{"label": _("Mark"), "fieldname": "mark", "fieldtype": "Link", "options": "Mark", "width": 110},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link", "options": "Grade", "width": 90},
	]

	# Stage 1 block
	columns += _stage_columns(stage_1, "s1")
	# Stage 2 block
	columns += _stage_columns(stage_2, "s2")

	# Difference block
	for field in NUMERIC_SCORE_FIELDS:
		columns.append(
			{
				"label": _(f"Δ {field.title()}"),
				"fieldname": f"diff_{field}",
				"fieldtype": "Int",
				"width": 100,
			}
		)

	return columns


def _stage_columns(stage, prefix):
	label = stage or ("Stage 1" if prefix == "s1" else "Stage 2")
	return [
		{
			"label": _(f"{label} - Taster"),
			"fieldname": f"{prefix}_taster",
			"fieldtype": "Link",
			"options": "Taster",
			"width": 120,
		},
		{"label": _(f"{label} - Colour"), "fieldname": f"{prefix}_colour", "fieldtype": "Int", "width": 100},
		{
			"label": _(f"{label} - Strength"),
			"fieldname": f"{prefix}_strength",
			"fieldtype": "Int",
			"width": 110,
		},
		{"label": _(f"{label} - Taste"), "fieldname": f"{prefix}_taste", "fieldtype": "Int", "width": 95},
		{
			"label": _(f"{label} - Briskness"),
			"fieldname": f"{prefix}_briskness",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _(f"{label} - Quality Grade"),
			"fieldname": f"{prefix}_quality_grade",
			"fieldtype": "Link",
			"options": "Quality Grade",
			"width": 140,
		},
	]


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("tea_lot"):
		conditions.append("tl.name = %(tea_lot)s")
		values["tea_lot"] = filters["tea_lot"]

	if filters.get("mark"):
		conditions.append("tl.mark = %(mark)s")
		values["mark"] = filters["mark"]

	if filters.get("grade"):
		conditions.append("tl.grade = %(grade)s")
		values["grade"] = filters["grade"]

	if filters.get("taster"):
		conditions.append("(s1.taster = %(taster)s OR s2.taster = %(taster)s)")
		values["taster"] = filters["taster"]

	if filters.get("from_date"):
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		values["to_date"] = filters["to_date"]

	if filters.get("from_date") or filters.get("to_date"):

		def build(clauses):
			return "(" + " AND ".join(clauses) + ")"

		s1_clauses = []
		s2_clauses = []
		if filters.get("from_date"):
			s1_clauses.append("s1.evaluation_date >= %(from_date)s")
			s2_clauses.append("s2.evaluation_date >= %(from_date)s")
		if filters.get("to_date"):
			s1_clauses.append("s1.evaluation_date <= %(to_date)s")
			s2_clauses.append("s2.evaluation_date <= %(to_date)s")

		conditions.append("(" + build(s1_clauses) + " OR " + build(s2_clauses) + ")")

	return conditions, values


def _latest_stage_join(alias, stage):
	"""Return a NOT EXISTS guard so at most one (latest) evaluation per stage/tea_lot is picked."""
	return f"""
		AND NOT EXISTS (
			SELECT 1 FROM `tabTea Evaluation` e2
			WHERE e2.tea_lot = {alias}.tea_lot
			  AND e2.evaluation_stage = %({alias}_stage)s
			  AND (e2.creation > {alias}.creation OR (e2.creation = {alias}.creation AND e2.name > {alias}.name))
		)
	"""


def get_data(filters, stage_1, stage_2):
	conditions, values = get_conditions(filters)
	where_clause = " AND ".join(conditions) if conditions else "1=1"

	values["s1_stage"] = stage_1
	values["s2_stage"] = stage_2

	data = frappe.db.sql(
		f"""
		SELECT
			tl.name AS tea_lot,
			tl.lot_no AS lot_no,
			tl.mark AS mark,
			tl.grade AS grade,
			s1.taster AS s1_taster,
			s1.colour AS s1_colour,
			s1.strength AS s1_strength,
			s1.taste AS s1_taste,
			s1.briskness AS s1_briskness,
			s1.quality_grade AS s1_quality_grade,
			s2.taster AS s2_taster,
			s2.colour AS s2_colour,
			s2.strength AS s2_strength,
			s2.taste AS s2_taste,
			s2.briskness AS s2_briskness,
			s2.quality_grade AS s2_quality_grade,
			s1.name AS s1_eval_name,
			s2.name AS s2_eval_name
		FROM `tabTea Lot` tl
		LEFT JOIN `tabTea Evaluation` s1
			ON s1.tea_lot = tl.name
		   AND s1.evaluation_stage = %(s1_stage)s
		   {_latest_stage_join("s1", stage_1)}
		LEFT JOIN `tabTea Evaluation` s2
			ON s2.tea_lot = tl.name
		   AND s2.evaluation_stage = %(s2_stage)s
		   {_latest_stage_join("s2", stage_2)}
		WHERE {where_clause}
		ORDER BY tl.creation DESC
		""",
		values,
		as_dict=True,
	)

	for row in data:
		for field in NUMERIC_SCORE_FIELDS:
			s1_val = row.get(f"s1_{field}")
			s2_val = row.get(f"s2_{field}")
			row[f"diff_{field}"] = _diff(s2_val, s1_val)

	return data


def _diff(stage_2_val, stage_1_val):
	if stage_2_val is None or stage_1_val is None:
		return None
	return stage_2_val - stage_1_val


def get_report_summary(data, stage_1, stage_2):
	total_lots = len(data)
	both_stages = 0
	only_s1 = 0
	only_s2 = 0
	stage_1_label = stage_1 or "Stage 1"
	stage_2_label = stage_2 or "Stage 2"

	for row in data:
		has_s1 = bool(row.get("s1_eval_name"))
		has_s2 = bool(row.get("s2_eval_name"))

		if has_s1 and has_s2:
			both_stages += 1
		elif has_s1:
			only_s1 += 1
		elif has_s2:
			only_s2 += 1

	return [
		{"label": _("Tea Lots (filtered)"), "value": total_lots, "indicator": "blue"},
		{"label": _("Both Stages Evaluated"), "value": both_stages, "indicator": "green"},
		{"label": _(f"Only {stage_1_label}"), "value": only_s1, "indicator": "orange"},
		{"label": _(f"Only {stage_2_label}"), "value": only_s2, "indicator": "purple"},
	]
