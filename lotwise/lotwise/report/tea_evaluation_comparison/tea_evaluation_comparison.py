# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _

NUMERIC_SCORE_FIELDS = ["colour", "strength", "taste", "briskness"]


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)
	summary = get_report_summary(data)

	# Skip Frappe's automatic total row since a comparison summary is added separately
	return columns, data, None, None, summary, 1


def get_columns():
	return [
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
		{"label": _("Taster"), "fieldname": "taster", "fieldtype": "Link", "options": "Taster", "width": 110},
		{"label": _("Bag Colour"), "fieldname": "bag_colour", "fieldtype": "Int", "width": 95},
		{"label": _("Bag Strength"), "fieldname": "bag_strength", "fieldtype": "Int", "width": 105},
		{"label": _("Bag Taste"), "fieldname": "bag_taste", "fieldtype": "Int", "width": 90},
		{"label": _("Bag Briskness"), "fieldname": "bag_briskness", "fieldtype": "Int", "width": 105},
		{
			"label": _("Bag Quality Grade"),
			"fieldname": "bag_quality_grade",
			"fieldtype": "Link",
			"options": "Quality Grade",
			"width": 130,
		},
		{"label": _("Pre-purchase Colour"), "fieldname": "pre_colour", "fieldtype": "Int", "width": 135},
		{"label": _("Pre-purchase Strength"), "fieldname": "pre_strength", "fieldtype": "Int", "width": 145},
		{"label": _("Pre-purchase Taste"), "fieldname": "pre_taste", "fieldtype": "Int", "width": 130},
		{
			"label": _("Pre-purchase Briskness"),
			"fieldname": "pre_briskness",
			"fieldtype": "Int",
			"width": 145,
		},
		{
			"label": _("Pre-purchase Quality Grade"),
			"fieldname": "pre_quality_grade",
			"fieldtype": "Link",
			"options": "Quality Grade",
			"width": 170,
		},
		{"label": _("Δ Colour"), "fieldname": "diff_colour", "fieldtype": "Int", "width": 90},
		{"label": _("Δ Strength"), "fieldname": "diff_strength", "fieldtype": "Int", "width": 100},
		{"label": _("Δ Taste"), "fieldname": "diff_taste", "fieldtype": "Int", "width": 85},
		{"label": _("Δ Briskness"), "fieldname": "diff_briskness", "fieldtype": "Int", "width": 100},
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
		conditions.append("(bs.taster = %(taster)s OR pp.taster = %(taster)s)")
		values["taster"] = filters["taster"]

	if filters.get("from_date"):
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		values["to_date"] = filters["to_date"]

	if filters.get("from_date") or filters.get("to_date"):

		def build(clauses):
			return "(" + " AND ".join(clauses) + ")"

		bs_clauses = []
		pp_clauses = []
		if filters.get("from_date"):
			bs_clauses.append("bs.evaluation_date >= %(from_date)s")
			pp_clauses.append("pp.evaluation_date >= %(from_date)s")
		if filters.get("to_date"):
			bs_clauses.append("bs.evaluation_date <= %(to_date)s")
			pp_clauses.append("pp.evaluation_date <= %(to_date)s")

		conditions.append("(" + build(bs_clauses) + " OR " + build(pp_clauses) + ")")

	return conditions, values


def _latest_stage_join(alias, stage):
	"""Return a NOT EXISTS guard so at most one (latest) evaluation per stage/tea_lot is picked."""
	return f"""
		AND NOT EXISTS (
			SELECT 1 FROM `tabTea Evaluation` e2
			WHERE e2.tea_lot = {alias}.tea_lot
			  AND e2.evaluation_stage = '{stage}'
			  AND (e2.creation > {alias}.creation OR (e2.creation = {alias}.creation AND e2.name > {alias}.name))
		)
	"""


def get_data(filters):
	conditions, values = get_conditions(filters)
	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(
		f"""
		SELECT
			tl.name AS tea_lot,
			tl.lot_no AS lot_no,
			tl.mark AS mark,
			tl.grade AS grade,
			COALESCE(bs.taster, pp.taster) AS taster,
			bs.colour AS bag_colour,
			bs.strength AS bag_strength,
			bs.taste AS bag_taste,
			bs.briskness AS bag_briskness,
			bs.quality_grade AS bag_quality_grade,
			pp.colour AS pre_colour,
			pp.strength AS pre_strength,
			pp.taste AS pre_taste,
			pp.briskness AS pre_briskness,
			pp.quality_grade AS pre_quality_grade,
			bs.name AS bag_eval_name,
			pp.name AS pre_eval_name
		FROM `tabTea Lot` tl
		LEFT JOIN `tabTea Evaluation` bs
			ON bs.tea_lot = tl.name
		   AND bs.evaluation_stage = 'Bag Sample'
		   {_latest_stage_join("bs", "Bag Sample")}
		LEFT JOIN `tabTea Evaluation` pp
			ON pp.tea_lot = tl.name
		   AND pp.evaluation_stage = 'Pre-purchase'
		   {_latest_stage_join("pp", "Pre-purchase")}
		WHERE {where_clause}
		ORDER BY tl.creation DESC
		""",
		values,
		as_dict=True,
	)

	for row in data:
		for field in NUMERIC_SCORE_FIELDS:
			bag_val = row.get(f"bag_{field}")
			pre_val = row.get(f"pre_{field}")
			row[f"diff_{field}"] = _diff(pre_val, bag_val)

	return data


def _diff(pre_val, bag_val):
	if pre_val is None or bag_val is None:
		return None
	return pre_val - bag_val


def get_report_summary(data):
	total_lots = len(data)
	both_stages = 0
	only_bag = 0
	only_pre = 0

	for row in data:
		has_bag = bool(row.get("bag_eval_name"))
		has_pre = bool(row.get("pre_eval_name"))

		if has_bag and has_pre:
			both_stages += 1
		elif has_bag:
			only_bag += 1
		elif has_pre:
			only_pre += 1

	return [
		{"label": _("Tea Lots (filtered)"), "value": total_lots, "indicator": "blue"},
		{"label": _("Both Stages Evaluated"), "value": both_stages, "indicator": "green"},
		{"label": _("Only Bag Sample"), "value": only_bag, "indicator": "orange"},
		{"label": _("Only Pre-purchase"), "value": only_pre, "indicator": "purple"},
	]
