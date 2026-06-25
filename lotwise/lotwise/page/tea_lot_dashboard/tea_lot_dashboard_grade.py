# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_lots_by_grade(grade: str) -> dict:
	"""
	Fetch Tea Lots linked with the selected Grade
	"""
	if not grade:
		return {"grade": "", "lots": []}

	grade = grade.strip()

	lots = frappe.db.sql(
		"""
		SELECT
			name,
			lot_no,
			mark,
			grade,
			invoice_number,
			liquor_mark,
			acquisition_channel,
			purchase_date,
			packages,
			net_weight_total,
			rate,
			status,
			holding_status
		FROM `tabTea Lot`
		WHERE docstatus < 2
			AND grade = %(grade)s
		ORDER BY creation DESC
		""",
		{"grade": grade},
		as_dict=True,
	)

	return {"grade": grade, "lots": lots}
