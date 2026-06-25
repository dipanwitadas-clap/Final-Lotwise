# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_lots_by_mark(mark: str) -> dict:
	"""
	Fetch Tea Lots linked with the selected Mark
	"""
	if not mark:
		return {"mark": "", "lots": []}

	mark = mark.strip()

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
			AND mark = %(mark)s
		ORDER BY creation DESC
		""",
		{"mark": mark},
		as_dict=True,
	)

	return {"mark": mark, "lots": lots}
