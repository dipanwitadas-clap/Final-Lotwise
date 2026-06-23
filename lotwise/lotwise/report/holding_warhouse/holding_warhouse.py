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


def get_columns():
	return [
		{"label": _("Lot ID"), "fieldname": "name", "fieldtype": "Link", "options": "Tea Lot", "width": 160},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 110},
		{"label": _("Channel"), "fieldname": "acquisition_channel", "fieldtype": "Data", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 105},
		{"label": _("Holding"), "fieldname": "holding_status", "fieldtype": "Data", "width": 110},
		{"label": _("Seller"), "fieldname": "seller", "fieldtype": "Link", "options": "Seller", "width": 150},
		{"label": _("Mark"), "fieldname": "mark", "fieldtype": "Link", "options": "Mark", "width": 130},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link", "options": "Grade", "width": 90},
		{
			"label": _("Segment"),
			"fieldname": "intended_segment",
			"fieldtype": "Link",
			"options": "Tea Segment",
			"width": 100,
		},
		{"label": _("Pkgs"), "fieldname": "packages", "fieldtype": "Int", "width": 80},
		{
			"label": _("Net Wt Kg"),
			"fieldname": "net_weight_total",
			"fieldtype": "Float",
			"precision": 2,
			"width": 100,
		},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 95},
		{"label": _("Warehouse"), "fieldname": "warehouselocation", "fieldtype": "Data", "width": 150},
		{"label": _("Purchase Date"), "fieldname": "purchase_date", "fieldtype": "Date", "width": 115},
		{"label": _("Invoice No"), "fieldname": "invoice_number", "fieldtype": "Data", "width": 120},
		{"label": _("GP No"), "fieldname": "gp_no", "fieldtype": "Data", "width": 95},
	]


def get_conditions(filters, table_alias=None):
	prefix = f"{table_alias}." if table_alias else ""
	conditions = [f"{prefix}holding_status in ('Committed','Received')"]
	values = {}

	filter_map = {
		"name": "name",
		"acquisition_channel": "acquisition_channel",
		"lot_no": "lot_no",
		"status": "status",
		"holding_status": "holding_status",
		"mark": "mark",
		"grade": "grade",
		"seller": "seller",
		"intended_segment": "intended_segment",
	}

	for key, field in filter_map.items():
		if filters.get(key):
			conditions.append(f"{prefix}{field} = %({key})s")
			values[key] = filters[key]

	if filters.get("from_date"):
		conditions.append(f"{prefix}purchase_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append(f"{prefix}purchase_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return conditions, values


def get_data(filters):
	conditions, values = get_conditions(filters, "tl")

	return frappe.db.sql(
		f"""
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
		""",
		values,
		as_dict=True,
	)


def get_report_summary(filters):
	conditions, values = get_conditions(filters)

	result = frappe.db.sql(
		f"""
		SELECT
			count(name) as total_lots,
			sum(packages) as total_packages,
			sum(net_weight_total) as total_weight,
			count(distinct mark) as total_marks,
			count(distinct seller) as total_sellers,
			sum(rate) as total_rate
		FROM `tabTea Lot`
		WHERE {" AND ".join(conditions)}
		""",
		values,
		as_dict=True,
	)[0]

	return [
		{"label": _("Total Lots"), "value": result.total_lots or 0, "indicator": "blue"},
		{"label": _("Total Packages"), "value": result.total_packages or 0, "indicator": "green"},
		{"label": _("Net Weight (Kg)"), "value": round(result.total_weight or 0, 2), "indicator": "orange"},
		{"label": _("Total Marks"), "value": result.total_marks or 0, "indicator": "purple"},
		{"label": _("Total Sellers"), "value": result.total_sellers or 0, "indicator": "red"},
		{"label": _("Total Rate"), "value": round(result.total_rate or 0, 2), "indicator": "yellow"},
	]
