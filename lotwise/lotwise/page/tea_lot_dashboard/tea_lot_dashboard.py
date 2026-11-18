# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# ============================================================
# DASHBOARD TOP SUMMARY CARDS
# ============================================================


@frappe.whitelist()
def get_summary_stats() -> dict:
	data = frappe.db.sql(
		"""
		SELECT

			COUNT(name) AS total_lots,

			COALESCE(SUM(packages),0)
			AS total_packages,

			COALESCE(SUM(net_weight_total),0)
			AS total_net_weight,

			COALESCE(SUM(net_weight_total * rate) / NULLIF(SUM(net_weight_total),0), 0)
			AS avg_rate,

			COUNT(DISTINCT mark)
			AS unique_marks,

			COUNT(DISTINCT grade)
			AS unique_grades


		FROM `tabTea Purchase`

		""",
		as_dict=True,
	)

	result = data[0] if data else {}

	result["total_evaluations"] = frappe.db.count("Tea Evaluation")

	return result


# ============================================================
# LOT DETAILS API
# ============================================================


@frappe.whitelist()
def get_lot_details(lot_no: str) -> dict:
	"""
	Fetch complete Tea Lot information
	and related Tea Evaluation details
	"""

	if not lot_no:
		frappe.throw(_("Please select Tea Lot"))

	raw_lot_no = lot_no
	clean_lot_no = lot_no.strip()

	lot_name = raw_lot_no

	if not frappe.db.exists("Tea Lot", lot_name):
		lot_name = clean_lot_no

	if not frappe.db.exists("Tea Lot", lot_name):
		lot_name = frappe.db.get_value("Tea Lot", {"lot_no": raw_lot_no}, "name")

	if not lot_name:
		lot_name = frappe.db.get_value("Tea Lot", {"lot_no": clean_lot_no}, "name")

	if not lot_name:
		matches = frappe.db.sql(
			"""
			SELECT name
			FROM `tabTea Lot`
			WHERE
				TRIM(name) = %(lot)s
				OR TRIM(lot_no) = %(lot)s
			ORDER BY creation DESC
			LIMIT 1
			""",
			{"lot": clean_lot_no},
			as_dict=True,
		)

		lot_name = matches[0].name if matches else None

	if not lot_name:
		frappe.throw(_("Tea Lot not found"))

	lot = frappe.get_doc("Tea Lot", lot_name)

	# -----------------------------
	# Tea Lot Information
	# -----------------------------

	lot_details = {
		"lot_id": lot.name,
		"lot_no": lot.lot_no,
		"acquisition_channel": lot.acquisition_channel,
		"seller": lot.seller,
		"mark": lot.mark,
		"grade": lot.grade,
		"packing": lot.packing,
		"intended_segment": lot.intended_segment,
		"packages": lot.packages,
		"gross_wtpkg": lot.gross_wtpkg,
		"net_wtpkg": lot.net_wtpkg,
		"net_weight_total": lot.net_weight_total,
		"rate": lot.rate,
		"status": lot.status,
		"purchase_status": lot.purchase_status,
		"liquor_mark": lot.liquor_mark,
		"density": lot.density,
		"invoice_number": lot.invoice_number,
		"warehouse": lot.warehouselocation,
		"purchase_date": lot.purchase_date,
		"gp_no": lot.gp_no,
		"gp_date": lot.gp_date,
		"awr_date": lot.awr_date,
		"sale_no": lot.sale_no,
		"broker": lot.broker,
		"auction_centre": lot.auction_centre,
		"division": lot.division,
		"manufacturer_ref": lot.manufacturer_ref,
		"chest_serial_range": lot.chest_serial_range,
		"certification": lot.certification,
		"mfg_monthyear": lot.mfg_monthyear,
		"blend": lot.blend,
		"do_reference": lot.do_reference,
		"do_date": lot.do_date,
		"source_doctype": lot.source_doctype,
		"source_doctype_id": lot.source_doctype_id,
	}

	# -----------------------------
	# Evaluation Details
	# -----------------------------

	evaluations = frappe.db.sql(
		"""
		SELECT

			name,

			taster,

			stage,

			evaluation_date,

			colour,

			strength,

			taste,

			briskness,

			quality_grade,

			suggested_valuation,

			notes


		FROM `tabTea Evaluation`


		WHERE tea_lot = %(lot)s


		ORDER BY creation DESC


		""",
		{"lot": lot_name},
		as_dict=True,
	)

	return {"lot_details": lot_details, "evaluations": evaluations}


# ============================================================
# LOT SEARCH QUERY
# ============================================================


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def lot_query(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict | None
) -> list:
	"""
	Search Tea Lot with useful information
	"""

	return frappe.db.sql(
		"""

		SELECT

			name,


			CONCAT(

				'Lot No: ',
				IFNULL(lot_no,name),

				' | ',

				'Mark: ',
				IFNULL(mark,'N/A'),


				' | Grade: ',
				IFNULL(grade,'N/A'),


				' | Seller: ',
				IFNULL(seller,'N/A'),


				' | Weight: ',
				IFNULL(net_weight_total,0),
				' Kg'

			)


		FROM `tabTea Lot`



		WHERE

			docstatus < 2


			AND

			(

				name LIKE %(txt)s

				OR TRIM(name) LIKE %(txt)s

				OR lot_no LIKE %(txt)s

				OR TRIM(lot_no) LIKE %(txt)s

				OR invoice_number LIKE %(txt)s

				OR mark LIKE %(txt)s

				OR grade LIKE %(txt)s

				OR seller LIKE %(txt)s

			)



		ORDER BY


			CASE

				WHEN name LIKE %(exact_txt)s
				THEN 1

				WHEN TRIM(name) LIKE %(exact_txt)s
				THEN 2

				WHEN lot_no LIKE %(exact_txt)s
				THEN 3

				WHEN TRIM(lot_no) LIKE %(exact_txt)s
				THEN 4

				ELSE 5

			END,


			creation DESC



		LIMIT %(start)s,%(page_len)s


		""",
		{"txt": f"%{txt}%", "exact_txt": f"{txt}%", "start": start, "page_len": page_len},
	)


# ============================================================
# DASHBOARD CHARTS (OPTIONAL)
# ============================================================


@frappe.whitelist()
def get_status_distribution() -> list:
	return frappe.db.sql(
		"""

		SELECT

			COALESCE(status,'Unknown')
			AS name,


			COUNT(*) AS value


		FROM `tabTea Lot`


		GROUP BY status


		ORDER BY value DESC


		""",
		as_dict=True,
	)


@frappe.whitelist()
def get_purchase_status_distribution() -> list:
	return frappe.db.sql(
		"""

		SELECT

			COALESCE(
				purchase_status,
				'Unknown'
			)
			AS name,


			COUNT(*) AS value


		FROM `tabTea Purchase`


		GROUP BY purchase_status


		ORDER BY value DESC


		""",
		as_dict=True,
	)
