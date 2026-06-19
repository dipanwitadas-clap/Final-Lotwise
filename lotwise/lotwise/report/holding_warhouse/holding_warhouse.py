# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()

	data = get_data(filters)

	summary = get_report_summary(filters)

	return columns, data, None, None, summary


# ---------------------------------------------------
# COLUMNS
# ---------------------------------------------------


def get_columns():
	return [
		{"label": _("Lot ID"), "fieldname": "name", "fieldtype": "Link", "options": "Tea Lot", "width": 120},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 100},
		{
			"label": _("Acquisition Channel"),
			"fieldname": "acquisition_channel",
			"fieldtype": "Data",
			"width": 130,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Holding Status"), "fieldname": "holding_status", "fieldtype": "Data", "width": 120},
		{"label": _("Seller"), "fieldname": "seller", "fieldtype": "Link", "options": "Seller", "width": 120},
		{"label": _("Mark"), "fieldname": "mark", "fieldtype": "Link", "options": "Mark", "width": 100},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link", "options": "Grade", "width": 100},
		{
			"label": _("Segment"),
			"fieldname": "intended_segment",
			"fieldtype": "Link",
			"options": "Tea Segment",
			"width": 120,
		},
		{"label": _("Packages"), "fieldname": "packages", "fieldtype": "Int", "width": 90},
		{
			"label": _("Net Weight Kg"),
			"fieldname": "net_weight_total",
			"fieldtype": "Float",
			"precision": 2,
			"width": 120,
		},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
		{"label": _("Warehouse"), "fieldname": "warehouselocation", "fieldtype": "Data", "width": 120},
		{"label": _("Purchase Date"), "fieldname": "purchase_date", "fieldtype": "Date", "width": 110},
		{"label": _("Invoice No"), "fieldname": "invoice_number", "fieldtype": "Data", "width": 120},
		{"label": _("GP No"), "fieldname": "gp_no", "fieldtype": "Data", "width": 100},
	]


# ---------------------------------------------------
# DATA
# ---------------------------------------------------


def get_data(filters):
	conditions = ["tl.holding_status in ('Committed','Received')"]

	values = {}

	filter_map = {
		"acquisition_channel": "tl.acquisition_channel",
		"lot_no": "tl.lot_no",
		"status": "tl.status",
		"holding_status": "tl.holding_status",
		"mark": "tl.mark",
		"grade": "tl.grade",
		"seller": "tl.seller",
		"intended_segment": "tl.intended_segment",
	}

	for key, field in filter_map.items():
		if filters.get(key):
			conditions.append(f"{field} = %({key})s")

			values[key] = filters[key]

	if filters.get("purchase_date"):
		conditions.append("tl.purchase_date = %(purchase_date)s")

		values["purchase_date"] = filters["purchase_date"]

	query = f"""

	SELECT

	tl.name,
	tl.lot_no,
	tl.acquisition_channel,
	tl.status,
	tl.holding_status,
	tl.seller,
	tl.mark,
	tl.grade,
	tl.intended_segment,
	tl.packages,
	tl.net_weight_total,
	tl.rate,
	tl.warehouselocation,
	tl.purchase_date,
	tl.invoice_number,
	tl.gp_no


	FROM `tabTea Lot` tl


	WHERE {" AND ".join(conditions)}


	ORDER BY tl.creation DESC


	"""

	return frappe.db.sql(query, values, as_dict=True)


# ---------------------------------------------------
# SUMMARY CARDS
# ---------------------------------------------------


def get_report_summary(filters):
	values = {}

	conditions = ["holding_status in ('Committed','Received')"]

	if filters.get("holding_status"):
		conditions.append("holding_status=%(holding_status)s")

		values["holding_status"] = filters["holding_status"]

	result = frappe.db.sql(
		f"""

		SELECT


		count(name) as total_lots,

		sum(packages) as total_packages,

		sum(net_weight_total) as total_weight,

		count(distinct mark) as total_marks,

		count(distinct seller) as total_sellers,

		avg(rate) as avg_rate


		FROM `tabTea Lot`


		WHERE {" AND ".join(conditions)}


		""",
		values,
		as_dict=True,
	)[0]

	return [
		{"label": "Total Lots", "value": result.total_lots or 0},
		{"label": "Total Packages", "value": result.total_packages or 0},
		{"label": "Net Weight (Kg)", "value": round(result.total_weight or 0, 2)},
		{"label": "Total Marks", "value": result.total_marks or 0},
		{"label": "Total Sellers", "value": result.total_sellers or 0},
		{"label": "Average Rate", "value": round(result.avg_rate or 0, 2)},
	]
