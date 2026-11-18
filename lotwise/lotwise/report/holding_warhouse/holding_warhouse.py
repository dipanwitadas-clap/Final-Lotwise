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
		{
			"label": _("Purchase ID"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Tea Purchase",
			"width": 160,
		},
		{
			"label": _("Tea Lot"),
			"fieldname": "tea_lot",
			"fieldtype": "Link",
			"options": "Tea Lot",
			"width": 160,
		},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 110},
		{"label": _("Season"), "fieldname": "season", "fieldtype": "Int", "width": 80},
		{"label": _("Sale No"), "fieldname": "sale_no", "fieldtype": "Int", "width": 90},
		{"label": _("Week No"), "fieldname": "week_no", "fieldtype": "Int", "width": 80},
		{"label": _("Deal No"), "fieldname": "deal_no", "fieldtype": "Data", "width": 110},
		{"label": _("Channel"), "fieldname": "acquisition_channel", "fieldtype": "Data", "width": 120},
		{
			"label": _("Auction Centre"),
			"fieldname": "auction_centre",
			"fieldtype": "Link",
			"options": "Auction Centre",
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
		{"label": _("Purchase Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 110},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 170,
		},
		{"label": _("Invoice No"), "fieldname": "invoice_number", "fieldtype": "Data", "width": 120},
		{"label": _("Broker"), "fieldname": "broker", "fieldtype": "Link", "options": "Broker", "width": 130},
	]


def get_conditions(filters, table_alias=None):
	prefix = f"{table_alias}." if table_alias else ""
	conditions = [f"{prefix}purchase_status IS NOT NULL"]
	values = {}

	filter_map = {
		"name": "tea_lot",
		"acquisition_channel": "acquisition_channel",
		"auction_centre": "auction_centre",
		"lot_no": "lot_no",
		"purchase_status": "purchase_status",
		"mark": "mark",
		"grade": "grade",
		"warehouse": "warehouse",
	}

	for key, field in filter_map.items():
		if filters.get(key):
			conditions.append(f"{prefix}{field} = %({key})s")
			values[key] = filters[key]

	if filters.get("sale_no_from"):
		conditions.append(f"{prefix}sale_no >= %(sale_no_from)s")
		values["sale_no_from"] = filters["sale_no_from"]

	if filters.get("sale_no_to"):
		conditions.append(f"{prefix}sale_no <= %(sale_no_to)s")
		values["sale_no_to"] = filters["sale_no_to"]

	return conditions, values


def get_data(filters):
	conditions, values = get_conditions(filters, "tp")

	where_clause = " AND ".join(conditions)

	data = frappe.db.sql(
		f"""
		SELECT
			tp.name,
			tp.tea_lot,
			tp.lot_no,
			tp.season,
			tp.sale_no,
			tp.week_no,
			tp.deal_no,
			tp.acquisition_channel,
			tp.auction_centre,
			tp.purchase_status,
			tp.mark,
			tp.grade,
			tp.packages,
			tp.net_weight_total,
			tp.rate,
			tp.net_weight_total * tp.rate AS total_amount,
			tp.warehouse,
			tp.invoice_number,
			tp.broker
		FROM `tabTea Purchase` tp
		WHERE {where_clause}
		ORDER BY tp.creation DESC
		""",
		values,
		as_dict=True,
	)

	# Add custom total row - sum numeric fields
	if data:
		total_row = {column["fieldname"]: None for column in get_columns()}
		total_row.update(
			{
				"name": "Total",
				"packages": sum(row.get("packages") or 0 for row in data),
				"net_weight_total": sum(row.get("net_weight_total") or 0 for row in data),
				"total_amount": sum(row.get("total_amount") or 0 for row in data),
			}
		)
		data.append(total_row)

	return data


def get_report_summary(filters):
	conditions, values = get_conditions(filters, "tp")

	where_clause = " AND ".join(conditions)

	result = frappe.db.sql(
		f"""
		SELECT
			count(tp.name) as total_lots,
			sum(tp.packages) as total_packages,
			sum(tp.net_weight_total) as total_weight,
			count(distinct tp.mark) as total_marks,
			COALESCE(SUM(tp.net_weight_total * tp.rate) / NULLIF(SUM(tp.net_weight_total),0), 0) AS avg_rate
		FROM `tabTea Purchase` tp
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
