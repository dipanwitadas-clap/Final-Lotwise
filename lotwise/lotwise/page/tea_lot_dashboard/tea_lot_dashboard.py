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

			COALESCE(AVG(rate),0)
			AS avg_rate,

			COUNT(DISTINCT mark)
			AS unique_marks,

			COUNT(DISTINCT grade)
			AS unique_grades


		FROM `tabTea Lot`

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
		"holding_status": lot.holding_status,
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
		"centre": lot.centre,
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
# MARK WISE LOTS API
# ============================================================


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
def get_holding_status_distribution() -> list:
	return frappe.db.sql(
		"""

		SELECT

			COALESCE(
				holding_status,
				'Unknown'
			)
			AS name,


			COUNT(*) AS value


		FROM `tabTea Lot`


		GROUP BY holding_status


		ORDER BY value DESC


		""",
		as_dict=True,
	)


@frappe.whitelist()
def get_evaluations(
	colour: str | None = None,
	strength: str | None = None,
	taste: str | None = None,
	briskness: str | None = None,
	quality_grade: str | None = None,
	taster: str | None = None,
	stage: str | None = None,
) -> dict:
	"""
	Fetch Tea Evaluations with optional filters
	"""
	conditions = []
	params = {}

	if colour is not None and colour != "":
		conditions.append("e.colour = %(colour)s")
		params["colour"] = float(colour)

	if strength is not None and strength != "":
		conditions.append("e.strength = %(strength)s")
		params["strength"] = float(strength)

	if taste is not None and taste != "":
		conditions.append("e.taste = %(taste)s")
		params["taste"] = float(taste)

	if briskness is not None and briskness != "":
		conditions.append("e.briskness = %(briskness)s")
		params["briskness"] = float(briskness)

	if quality_grade is not None and quality_grade != "":
		conditions.append("e.quality_grade = %(quality_grade)s")
		params["quality_grade"] = quality_grade

	if taster is not None and taster != "":
		conditions.append("e.taster = %(taster)s")
		params["taster"] = taster

	if stage is not None and stage != "":
		conditions.append("e.stage = %(stage)s")
		params["stage"] = stage

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	evaluations = frappe.db.sql(
		f"""
		SELECT
			e.name,
			e.tea_lot,
			e.taster,
			e.stage,
			e.evaluation_date,
			e.colour,
			e.strength,
			e.taste,
			e.briskness,
			e.quality_grade,
			e.suggested_valuation,
			e.notes,
			tl.lot_no AS tea_lot_no,
			tl.mark AS tea_lot_mark
		FROM `tabTea Evaluation` e
		LEFT JOIN `tabTea Lot` tl ON tl.name = e.tea_lot
		WHERE {where_clause}
		ORDER BY e.creation DESC
		""",
		params,
		as_dict=True,
	)

	return {"evaluations": evaluations}


@frappe.whitelist()
def get_quality_distribution() -> list:
	return frappe.db.sql(
		"""

		SELECT

			COALESCE(
				quality_grade,
				'Unrated'
			)
			AS name,


			COUNT(*) AS value


		FROM `tabTea Evaluation`


		GROUP BY quality_grade


		ORDER BY value DESC


		""",
		as_dict=True,
	)
