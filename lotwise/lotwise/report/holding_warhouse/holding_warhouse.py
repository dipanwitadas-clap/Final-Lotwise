# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)
	summary = get_report_summary(filters)

	# Skip Frappe's automatic total row since we added our own custom one
	return columns, data, None, None, summary, 1


def get_columns():
	return [
		{"label": _("Lot ID"), "fieldname": "name", "fieldtype": "Link", "options": "Tea Lot", "width": 160},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 110},
		{"label": _("Sale No"), "fieldname": "sale_no", "fieldtype": "Int", "width": 90},
		{"label": _("Channel"), "fieldname": "acquisition_channel", "fieldtype": "Data", "width": 120},
		{
			"label": _("Auction Centre"),
			"fieldname": "auction_centre",
			"fieldtype": "Link",
			"options": "Auction Centre",
			"width": 150,
		},
		{
			"label": _("Evaluation Status"),
			"fieldname": "evaluation_status",
			"fieldtype": "Link",
			"options": "Evaluation Status",
			"width": 150,
		},
		{
			"label": _("Purchase Status"),
			"fieldname": "purchase_status",
			"fieldtype": "Link",
			"options": "Purchase Status",
			"width": 130,
		},
		{"label": _("Mark"), "fieldname": "mark", "fieldtype": "Link", "options": "Mark", "width": 130},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link", "options": "Grade", "width": 90},
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
		{"label": _("Purchase From"), "fieldname": "purchase_from", "fieldtype": "Data", "width": 130},
		{
			"label": _("Purchase Invoice No"),
			"fieldname": "purchase_invoice_no",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount_as_per_to_tax_invoice",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("Density"), "fieldname": "density", "fieldtype": "Float", "precision": 2, "width": 95},
		{
			"label": _("Liquor Mark"),
			"fieldname": "liquor_mark",
			"fieldtype": "Link",
			"options": "Liquor Mark",
			"width": 130,
		},
	]


def get_conditions(filters, table_alias=None):
	prefix = f"{table_alias}." if table_alias else ""
	conditions = [f"{prefix}purchase_status IS NOT NULL"]
	values = {}

	filter_map = {
		"name": "name",
		"acquisition_channel": "acquisition_channel",
		"auction_centre": "auction_centre",
		"lot_no": "lot_no",
		"evaluation_status": "evaluation_status",
		"purchase_status": "purchase_status",
		"mark": "mark",
		"grade": "grade",
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

	if filters.get("sale_no_from"):
		conditions.append(f"{prefix}sale_no >= %(sale_no_from)s")
		values["sale_no_from"] = filters["sale_no_from"]

	if filters.get("sale_no_to"):
		conditions.append(f"{prefix}sale_no <= %(sale_no_to)s")
		values["sale_no_to"] = filters["sale_no_to"]

	return conditions, values


def get_data(filters):
	conditions, values = get_conditions(filters, "tl")

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(
		f"""
		SELECT
			tl.name,
			tl.lot_no,
			tl.sale_no,
			tl.acquisition_channel,
			tl.auction_centre,
			tl.evaluation_status,
			tl.purchase_status,
			tl.mark,
			tl.grade,
			tl.packages,
			tl.net_weight_total,
			tl.rate,
			tl.warehouselocation,
			tl.purchase_date,
			tl.invoice_number,
			tl.gp_no,
			tl.purchase_from,
			tl.purchase_invoice_no,
			tl.total_amount_as_per_to_tax_invoice,
			tl.density,
			tl.liquor_mark
		FROM `tabTea Lot` tl
		WHERE {where_clause}
		ORDER BY tl.creation DESC
		""",
		values,
		as_dict=True,
	)

	# Add custom total row - sum numeric fields
	if data:
		total_row = {
			"name": "Total",
			"lot_no": None,
			"sale_no": None,
			"acquisition_channel": None,
			"auction_centre": None,
			"evaluation_status": None,
			"purchase_status": None,
			"mark": None,
			"grade": None,
			"packages": sum(row.get("packages") or 0 for row in data),
			"net_weight_total": sum(row.get("net_weight_total") or 0 for row in data),
			"rate": sum(row.get("rate") or 0 for row in data),
			"warehouselocation": None,
			"purchase_date": None,
			"invoice_number": None,
			"gp_no": None,
			"purchase_from": None,
			"purchase_invoice_no": None,
			"total_amount_as_per_to_tax_invoice": sum(
				row.get("total_amount_as_per_to_tax_invoice") or 0 for row in data
			),
			"density": None,
			"liquor_mark": None,
		}
		data.append(total_row)

	return data


def get_report_summary(filters):
	conditions, values = get_conditions(filters)

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	result = frappe.db.sql(
		f"""
		SELECT
			count(name) as total_lots,
			sum(packages) as total_packages,
			sum(net_weight_total) as total_weight,
			count(distinct mark) as total_marks,
			COALESCE(SUM(net_weight_total * rate) / NULLIF(SUM(net_weight_total),0), 0) AS avg_rate
		FROM `tabTea Lot`
		WHERE {where_clause}
		""",
		values,
		as_dict=True,
	)[0]

	return [
		{"label": _("Total Lots"), "value": result.total_lots or 0, "indicator": "blue"},
		{"label": _("Total Packages"), "value": result.total_packages or 0, "indicator": "green"},
		{
			"label": _("Net Weight (Kg)"),
			"value": "{:,.2f}".format(round(result.total_weight or 0, 2)),
			"indicator": "orange",
		},
		{"label": _("Total Marks"), "value": result.total_marks or 0, "indicator": "purple"},
		{"label": _("Avg Rate/kg"), "value": round(result.avg_rate or 0, 2), "indicator": "yellow"},
	]
