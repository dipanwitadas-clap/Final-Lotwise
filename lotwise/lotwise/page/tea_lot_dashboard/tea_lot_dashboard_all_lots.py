# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl


@frappe.whitelist()
def get_all_lots(from_date: str | None = None, to_date: str | None = None) -> dict:
	"""
	Fetch all Tea Lots for the main Tea Lot tab.
	Optional date range filter on purchase_date.
	"""
	conditions = ["docstatus < 2"]
	values = {}

	if from_date:
		conditions.append("purchase_date >= %(from_date)s")
		values["from_date"] = from_date

	if to_date:
		conditions.append("purchase_date <= %(to_date)s")
		values["to_date"] = to_date

	lots = frappe.db.sql(
		f"""
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
		WHERE {" AND ".join(conditions)}
		ORDER BY creation DESC
		""",
		values,
		as_dict=True,
	)

	return {"lots": lots}
