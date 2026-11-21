# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

"""Buying Overview tab: buying week / buying day / lot / purchase / PO / evaluation."""

import json

import frappe

# Tea Lot is the base for lot metrics (so Offer lots with no purchase yet are
# counted). Buying Day/Week come through Tea Lot.source_doctype_id; purchase and
# PO figures come from Tea Purchase (tp.tea_lot = tl.name) / Purchase Order.
_FROM = """
	FROM `tabTea Lot` tl
	LEFT JOIN `tabBuying Day` bd
		ON tl.source_doctype = 'Buying Day' AND tl.source_doctype_id = bd.name
	LEFT JOIN `tabBuying Week` bw ON bw.name = bd.buying_week
	LEFT JOIN `tabTea Purchase` tp ON tp.tea_lot = tl.name
	LEFT JOIN `tabPurchase Order` po ON po.name = tp.purchase_order
"""

# Buying Day is the base; used for day/week counts and tables so days with no
# lots yet are still listed.
_FROM_DAY = """
	FROM `tabBuying Day` bd
	LEFT JOIN `tabBuying Week` bw ON bw.name = bd.buying_week
	LEFT JOIN `tabTea Lot` tl
		ON tl.source_doctype = 'Buying Day' AND tl.source_doctype_id = bd.name
	LEFT JOIN `tabTea Purchase` tp ON tp.tea_lot = tl.name
	LEFT JOIN `tabPurchase Order` po ON po.name = tp.purchase_order
"""

_EVALUATED = "EXISTS (SELECT 1 FROM `tabTea Evaluation` te WHERE te.tea_lot = tl.name)"


def _parse(filters):
	if isinstance(filters, str):
		filters = json.loads(filters or "{}")
	return filters or {}


def _where(filters, channel_col="tl.acquisition_channel"):
	filters = _parse(filters)
	conds, values = ["1=1"], {}
	if filters.get("season"):
		conds.append("bd.season = %(season)s")
		values["season"] = filters["season"]
	if filters.get("buying_week"):
		conds.append("bd.buying_week = %(buying_week)s")
		values["buying_week"] = filters["buying_week"]
	if filters.get("buying_day"):
		conds.append("bd.name = %(buying_day)s")
		values["buying_day"] = filters["buying_day"]
	if filters.get("acquisition_channel"):
		conds.append(f"{channel_col} = %(acquisition_channel)s")
		values["acquisition_channel"] = filters["acquisition_channel"]
	if filters.get("purchase_status"):
		conds.append("tl.purchase_status = %(purchase_status)s")
		values["purchase_status"] = filters["purchase_status"]
	if filters.get("po_status"):
		conds.append("po.status = %(po_status)s")
		values["po_status"] = filters["po_status"]
	return " AND ".join(conds), values


def _where_day(filters):
	"""Day/week driven: channel is the day's own channel; lot-level filters
	(purchase/PO status) keep only days that have matching lots."""
	return _where(filters, channel_col="bd.acquisition_channel")


@frappe.whitelist()
def get_filter_options(buying_week: str | None = None) -> dict:
	day_filters = {"buying_week": buying_week} if buying_week else {}
	days = frappe.get_all(
		"Buying Day",
		filters=day_filters,
		fields=["name", "day", "week_no", "status"],
		order_by="week_no desc, day asc",
		limit=500,
	)
	return {
		"seasons": [
			r[0]
			for r in frappe.db.sql(
				"SELECT DISTINCT season FROM `tabBuying Week` WHERE season IS NOT NULL ORDER BY season DESC"
			)
		],
		"weeks": frappe.get_all(
			"Buying Week",
			fields=["name", "week_no", "season", "acquisition_channel"],
			order_by="season desc, week_no desc",
			limit=500,
		),
		"days": days,
		"purchase_statuses": frappe.get_all("Purchase Status", pluck="name"),
		"po_statuses": [
			"Draft",
			"To Receive and Bill",
			"To Bill",
			"To Receive",
			"Completed",
			"Cancelled",
			"Closed",
		],
	}


@frappe.whitelist()
def get_kpis(filters=None) -> dict:
	where, v = _where(filters)
	row = frappe.db.sql(
		f"""
		SELECT
			COUNT(DISTINCT tl.name) AS lots,
			COALESCE(SUM(tl.packages), 0) AS packages,
			COALESCE(SUM(tl.net_weight_total), 0) AS net_weight,
			COUNT(DISTINCT tp.name) AS purchased_lots,
			COALESCE(SUM(tp.net_weight_total * tp.rate), 0) AS value,
			COALESCE(SUM(tp.net_weight_total * tp.rate) / NULLIF(SUM(tp.net_weight_total), 0), 0) AS avg_rate,
			COUNT(DISTINCT tp.purchase_order) AS po_count,
			COUNT(DISTINCT CASE WHEN {_EVALUATED} THEN tl.name END) AS evaluated
		{_FROM} WHERE {where}
		""",
		v,
		as_dict=True,
	)[0]
	dwhere, dv = _where_day(filters)
	row.update(
		frappe.db.sql(
			f"""
			SELECT COUNT(DISTINCT bd.name) AS buying_days,
				COUNT(DISTINCT bd.buying_week) AS buying_weeks
			{_FROM_DAY} WHERE {dwhere}
			""",
			dv,
			as_dict=True,
		)[0]
	)
	row["not_evaluated"] = (row["lots"] or 0) - (row["evaluated"] or 0)
	# PO total over distinct POs (SUM(DISTINCT) would drop equal amounts)
	row["po_total"] = frappe.db.sql(
		f"""
		SELECT COALESCE(SUM(x.grand_total), 0) FROM (
			SELECT DISTINCT po.name, po.grand_total {_FROM}
			WHERE {where} AND po.name IS NOT NULL
		) x
		""",
		v,
	)[0][0]
	return row


@frappe.whitelist()
def get_week_summary(filters=None) -> list:
	where, v = _where_day(filters)
	return frappe.db.sql(
		f"""
		SELECT
			bd.buying_week AS buying_week,
			MAX(bw.week_no) AS week_no,
			MAX(bw.season) AS season,
			COUNT(DISTINCT bd.name) AS days,
			COUNT(DISTINCT tl.name) AS lots,
			COALESCE(SUM(tl.net_weight_total), 0) AS net_weight,
			COUNT(DISTINCT tp.name) AS purchased_lots,
			COALESCE(SUM(tp.net_weight_total * tp.rate), 0) AS value,
			COUNT(DISTINCT tp.purchase_order) AS pos,
			(SELECT COUNT(*) FROM `tabBuying Week Tea` t
				JOIN `tabBuying Day` d ON d.name = t.parent
				WHERE d.buying_week = bd.buying_week) AS catalogue_rows
		{_FROM_DAY} WHERE {where} AND bd.buying_week IS NOT NULL
		GROUP BY bd.buying_week
		ORDER BY MAX(bw.season) DESC, MAX(bw.week_no) DESC
		""",
		v,
		as_dict=True,
	)


@frappe.whitelist()
def get_day_summary(filters=None) -> list:
	where, v = _where_day(filters)
	return frappe.db.sql(
		f"""
		SELECT
			bd.name AS buying_day, bd.buying_week, bd.day, bd.status,
			bd.acquisition_channel,
			COUNT(DISTINCT tl.name) AS lots,
			COALESCE(SUM(tl.net_weight_total), 0) AS net_weight,
			COUNT(DISTINCT tp.name) AS purchased_lots,
			COALESCE(SUM(tp.net_weight_total * tp.rate), 0) AS value,
			COUNT(DISTINCT tp.purchase_order) AS pos,
			COUNT(DISTINCT CASE WHEN {_EVALUATED} THEN tl.name END) AS evaluated,
			(SELECT COUNT(*) FROM `tabBuying Week Tea` t WHERE t.parent = bd.name) AS catalogue_rows
		{_FROM_DAY} WHERE {where}
		GROUP BY bd.name, bd.buying_week, bd.day, bd.status, bd.acquisition_channel
		ORDER BY bd.buying_week DESC, bd.day ASC
		""",
		v,
		as_dict=True,
	)


@frappe.whitelist()
def get_channel_split(filters=None) -> list:
	where, v = _where(filters)
	return frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(tl.acquisition_channel, ''), 'Unspecified') AS channel,
			COUNT(DISTINCT tl.name) AS lots,
			COALESCE(SUM(tl.net_weight_total), 0) AS net_weight,
			COALESCE(SUM(tp.net_weight_total * tp.rate), 0) AS value
		{_FROM} WHERE {where}
		GROUP BY channel ORDER BY lots DESC
		""",
		v,
		as_dict=True,
	)


@frappe.whitelist()
def get_po_summary(filters=None) -> list:
	where, v = _where(filters)
	return frappe.db.sql(
		f"""
		SELECT
			po.name AS purchase_order, po.supplier, po.status, po.transaction_date,
			po.grand_total, po.per_received, po.per_billed,
			COUNT(DISTINCT tp.name) AS lots,
			COALESCE(SUM(tp.net_weight_total), 0) AS net_weight,
			MAX(bd.name) AS buying_day
		{_FROM} WHERE {where} AND po.name IS NOT NULL
		GROUP BY po.name, po.supplier, po.status, po.transaction_date,
			po.grand_total, po.per_received, po.per_billed
		ORDER BY po.transaction_date DESC, po.name DESC
		LIMIT 500
		""",
		v,
		as_dict=True,
	)


@frappe.whitelist()
def get_lot_rows(filters=None) -> list:
	"""Lot-wise rows (all Tea Lots) with latest evaluation."""
	where, v = _where(filters)
	return frappe.db.sql(
		f"""
		SELECT
			tp.name AS tea_purchase, tl.name AS tea_lot, tl.lot_no, tl.mark, tl.grade,
			tl.acquisition_channel, tl.purchase_status, tl.packages,
			tl.net_weight_total, tp.rate AS rate, tp.purchase_order,
			bd.name AS buying_day, bd.buying_week,
			po.status AS po_status,
			(SELECT COUNT(*) FROM `tabTea Evaluation` te WHERE te.tea_lot = tl.name) AS eval_count,
			(SELECT te.evaluation_stage FROM `tabTea Evaluation` te WHERE te.tea_lot = tl.name
				ORDER BY te.evaluation_date DESC, te.creation DESC LIMIT 1) AS eval_stage,
			(SELECT te.suggested_valuation FROM `tabTea Evaluation` te WHERE te.tea_lot = tl.name
				ORDER BY te.evaluation_date DESC, te.creation DESC LIMIT 1) AS suggested_valuation
		{_FROM} WHERE {where}
		ORDER BY bd.buying_week DESC, bd.day ASC, tl.lot_no
		LIMIT 5000
		""",
		v,
		as_dict=True,
	)
