# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_all_lots() -> dict:
	"""
	Fetch all Tea Lots for the main Tea Lot tab
	"""
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
			holding_status,
			seller,
			warehouselocation AS warehouse
		FROM `tabTea Lot`
		WHERE docstatus < 2
		ORDER BY creation DESC
		""",
		as_dict=True,
	)

	return {"lots": lots}
