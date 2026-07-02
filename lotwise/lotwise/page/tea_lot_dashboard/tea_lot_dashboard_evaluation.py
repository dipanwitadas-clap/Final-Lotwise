# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_evaluations(
	colour: str | None = None,
	colour_operator: str | None = None,
	strength: str | None = None,
	strength_operator: str | None = None,
	taste: str | None = None,
	taste_operator: str | None = None,
	briskness: str | None = None,
	briskness_operator: str | None = None,
	quality_grade: str | None = None,
	taster: str | None = None,
	stage: str | None = None,
) -> dict:
	"""
	Fetch Tea Evaluations with optional filters
	"""
	conditions = []
	params = {}

	if colour is not None and colour != "":
		op = colour_operator or "="
		conditions.append(f"e.colour {op} %(colour)s")
		params["colour"] = float(colour)

	if strength is not None and strength != "":
		op = strength_operator or "="
		conditions.append(f"e.strength {op} %(strength)s")
		params["strength"] = float(strength)

	if taste is not None and taste != "":
		op = taste_operator or "="
		conditions.append(f"e.taste {op} %(taste)s")
		params["taste"] = float(taste)

	if briskness is not None and briskness != "":
		op = briskness_operator or "="
		conditions.append(f"e.briskness {op} %(briskness)s")
		params["briskness"] = float(briskness)

	if quality_grade is not None and quality_grade != "":
		conditions.append("e.quality_grade = %(quality_grade)s")
		params["quality_grade"] = quality_grade

	if taster is not None and taster != "":
		conditions.append("e.taster = %(taster)s")
		params["taster"] = taster

	if stage is not None and stage != "":
		conditions.append("e.stage = %(stage)s")
		params["stage"] = stage

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	evaluations = frappe.db.sql(
		f"""
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
		WHERE {where_clause}
		ORDER BY e.creation DESC
		""",
		params,
		as_dict=True,
	)

	return {"evaluations": evaluations}
