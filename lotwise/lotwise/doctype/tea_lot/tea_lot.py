# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io

import frappe
import openpyxl
from frappe.model.document import Document
from frappe.utils import flt


class TeaLot(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		awr_date: DF.Date | None
		blend: DF.Literal["", "PREMIUM PACK"]
		broker: DF.Link | None
		centre: DF.Data | None
		certification: DF.Data | None
		chest_serial_range: DF.Data | None
		density: DF.Float
		division: DF.Data | None
		do_date: DF.Data | None
		do_reference: DF.Data | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		grade: DF.Link | None
		gross_wtpkg: DF.Float
		holding_status: DF.Literal["", "Committed", "Received", "In Stock"]
		intended_segment: DF.Link | None
		invoice_number: DF.Data
		liquor_mark: DF.Literal["", "A+", "A", "B+", "B", "C+", "C"]
		lot_no: DF.Data | None
		manufacturer_ref: DF.Data | None
		mark: DF.Link
		mfg_monthyear: DF.Data | None
		net_weight_total: DF.Float
		net_wtpkg: DF.Float
		packages: DF.Int
		packing: DF.Link | None
		purchase_date: DF.Date | None
		purchase_from: DF.Data | None
		purchase_invoice_date: DF.Date | None
		purchase_invoice_no: DF.Data | None
		rate: DF.Currency
		sale_no: DF.Data | None
		seller: DF.Link | None
		source_doctype: DF.Link | None
		source_doctype_id: DF.DynamicLink | None
		status: DF.Literal["", "Offered", "Evaluated"]
		total_amount_as_per_to_tax_invoice: DF.Float
		warehouse_name: DF.Data | None
		warehouselocation: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot"


# ============================================================
# HELPERS
# ============================================================


def get_evaluation_field_options(fieldname: str) -> list:
	"""
	Fetch the Select options for a given fieldname from Tea Evaluation doctype.
	Options are stored as newline-separated values in DocField.
	Returns a list of option strings (empty string and blank ones filtered out).
	"""
	options_str = frappe.db.get_value(
		"DocField",
		{"parent": "Tea Evaluation", "fieldname": fieldname},
		"options",
	)

	if not options_str:
		return []

	# Options are stored as "\nOption1\nOption2\n..."
	# Split by newline and filter out empty / whitespace-only entries
	options = [opt.strip() for opt in options_str.split("\n") if opt.strip()]

	return options


# ============================================================
# XLSX DOWNLOAD - EVALUATION IMPORT
# ============================================================


@frappe.whitelist()
def download_evaluation_import_xlsx() -> dict:
	"""
	Generate xlsx with Tea Lots where status != 'Evaluated'.
	First 3 columns (Tea Lot, Mark, Invoice Number) have data,
	remaining columns have headers only (blank data).

	Stage (col 5), Liquor Mark (col 6), and Quality Grade (col 12)
	have Excel dropdown validation with options dynamically fetched
	from Tea Evaluation doctype field definitions.

	Dropdown options are stored in hidden columns (P, Q, R) on the
	same sheet and referenced via same-sheet range formulas for
	maximum Excel compatibility.
	"""
	# Fetch unevaluated Tea Lots
	lots = frappe.db.sql(
		"""
		SELECT name, mark, invoice_number
		FROM `tabTea Lot`
		WHERE status != "Evaluated" OR status IS NULL
		ORDER BY creation DESC
		""",
		as_dict=True,
	)

	# Fetch dropdown options dynamically from Tea Evaluation doctype
	stage_options = get_evaluation_field_options("stage")
	liquor_mark_options = get_evaluation_field_options("liquor_mark")
	quality_grade_options = get_evaluation_field_options("quality_grade")

	# Fixed 0-10 options for Colour, Strength, Taste, Briskness
	numeric_options = [str(i) for i in range(0, 11)]  # ["0","1",...,"10"]

	# Create workbook
	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "Evaluations"

	# ============================================================
	# Headers
	# ============================================================
	# Column indices (1-based):
	#  1: Tea Lot
	#  2: Mark
	#  3: Invoice Number
	#  4: Taster
	#  5: Stage        <-- dropdown
	#  6: Liquor Mark  <-- dropdown
	#  7: Colour
	#  8: Strength
	#  9: Taste
	# 10: Briskness
	# 11: Quality Grade <-- dropdown
	# 12: Suggested Valuation
	# 13: Notes
	# 14: Evaluation Date (DD-MM-YYYY)
	headers = [
		"Tea Lot",
		"Mark",
		"Invoice Number",
		"Taster",
		"Stage",
		"Liquor Mark",
		"Colour",
		"Strength",
		"Taste",
		"Briskness",
		"Quality Grade",
		"Suggested Valuation",
		"Notes",
		"Evaluation Date (DD-MM-YYYY)",
	]

	# Write headers
	for col_idx, header in enumerate(headers, 1):
		ws.cell(row=1, column=col_idx, value=header)

	# Write data rows (only Tea Lot, Mark, Invoice Number filled)
	for row_idx, lot in enumerate(lots, 2):
		ws.cell(row=row_idx, column=1, value=lot.name)
		ws.cell(row=row_idx, column=2, value=lot.mark)
		ws.cell(row=row_idx, column=3, value=lot.invoice_number)
		# Columns 4-15 remain blank (already None by default)

	# ============================================================
	# Write dropdown options in hidden columns (P=16, Q=17, R=18)
	# Same-sheet references are most reliable for Excel data validation
	# ============================================================

	# Column P (16): Stage options starting from row 2
	for idx, opt in enumerate(stage_options, 2):
		ws.cell(row=idx, column=16, value=opt)
	stage_last_row = len(stage_options) + 1
	if stage_last_row < 2:
		stage_last_row = 2

	# Column Q (17): Liquor Mark options starting from row 2
	for idx, opt in enumerate(liquor_mark_options, 2):
		ws.cell(row=idx, column=17, value=opt)
	liquor_last_row = len(liquor_mark_options) + 1
	if liquor_last_row < 2:
		liquor_last_row = 2

	# Column R (18): Quality Grade options starting from row 2
	for idx, opt in enumerate(quality_grade_options, 2):
		ws.cell(row=idx, column=18, value=opt)
	grade_last_row = len(quality_grade_options) + 1
	if grade_last_row < 2:
		grade_last_row = 2

	# Hide columns P, Q, R so users don't see the options data
	ws.column_dimensions["P"].hidden = True
	ws.column_dimensions["Q"].hidden = True
	ws.column_dimensions["R"].hidden = True

	# ============================================================
	# Write dropdown options in hidden columns (S=19, T=20, U=21, V=22)
	# for Colour, Strength, Taste, Briskness (0-10)
	# ============================================================

	# Column S (19): Colour options (0-10) starting from row 2
	for idx, opt in enumerate(numeric_options, 2):
		ws.cell(row=idx, column=19, value=opt)
	numeric_last_row = len(numeric_options) + 1  # = 11 + 1 = 12

	# Column T (20): Strength options (0-10) starting from row 2
	for idx, opt in enumerate(numeric_options, 2):
		ws.cell(row=idx, column=20, value=opt)

	# Column U (21): Taste options (0-10) starting from row 2
	for idx, opt in enumerate(numeric_options, 2):
		ws.cell(row=idx, column=21, value=opt)

	# Column V (22): Briskness options (0-10) starting from row 2
	for idx, opt in enumerate(numeric_options, 2):
		ws.cell(row=idx, column=22, value=opt)

	# Hide columns S, T, U, V so users don't see the options data
	ws.column_dimensions["S"].hidden = True
	ws.column_dimensions["T"].hidden = True
	ws.column_dimensions["U"].hidden = True
	ws.column_dimensions["V"].hidden = True

	# ============================================================
	# Add Data Validation (Dropdown) using same-sheet references
	# ============================================================

	last_data_row = len(lots) + 1  # +1 for header row
	if last_data_row < 2:
		last_data_row = 2  # at least cover row 2 even if no data

	# Column 5 (E): Stage - reference $P$2:$P${stage_last_row}
	if stage_options:
		stage_range = f"$P$2:$P${stage_last_row}"
		stage_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=stage_range,
			allow_blank=True,
		)
		stage_dv.error = "Please select a valid Stage value from the dropdown."
		stage_dv.errorTitle = "Invalid Stage"
		stage_dv.prompt = "Select Stage from the list"
		stage_dv.promptTitle = "Stage"
		ws.add_data_validation(stage_dv)
		stage_dv.add(f"E2:E{last_data_row}")

	# Column 6 (F): Liquor Mark - reference $Q$2:$Q${liquor_last_row}
	if liquor_mark_options:
		liquor_range = f"$Q$2:$Q${liquor_last_row}"
		liquor_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=liquor_range,
			allow_blank=True,
		)
		liquor_dv.error = "Please select a valid Liquor Mark value from the dropdown."
		liquor_dv.errorTitle = "Invalid Liquor Mark"
		liquor_dv.prompt = "Select Liquor Mark from the list"
		liquor_dv.promptTitle = "Liquor Mark"
		ws.add_data_validation(liquor_dv)
		liquor_dv.add(f"F2:F{last_data_row}")

	# Column 11 (K): Quality Grade - reference $R$2:$R${grade_last_row}
	if quality_grade_options:
		grade_range = f"$R$2:$R${grade_last_row}"
		grade_dv = openpyxl.worksheet.datavalidation.DataValidation(
			type="list",
			formula1=grade_range,
			allow_blank=True,
		)
		grade_dv.error = "Please select a valid Quality Grade value from the dropdown."
		grade_dv.errorTitle = "Invalid Quality Grade"
		grade_dv.prompt = "Select Quality Grade from the list"
		grade_dv.promptTitle = "Quality Grade"
		ws.add_data_validation(grade_dv)
		grade_dv.add(f"K2:K{last_data_row}")

	# Column 7 (G): Colour - reference $S$2:$S${numeric_last_row}
	colour_range = f"$S$2:$S${numeric_last_row}"
	colour_dv = openpyxl.worksheet.datavalidation.DataValidation(
		type="list",
		formula1=colour_range,
		allow_blank=True,
	)
	colour_dv.error = "Please select a valid Colour value from the dropdown."
	colour_dv.errorTitle = "Invalid Colour"
	colour_dv.prompt = "Select Colour (0-10) from the list"
	colour_dv.promptTitle = "Colour"
	ws.add_data_validation(colour_dv)
	colour_dv.add(f"G2:G{last_data_row}")

	# Column 8 (H): Strength - reference $T$2:$T${numeric_last_row}
	strength_range = f"$T$2:$T${numeric_last_row}"
	strength_dv = openpyxl.worksheet.datavalidation.DataValidation(
		type="list",
		formula1=strength_range,
		allow_blank=True,
	)
	strength_dv.error = "Please select a valid Strength value from the dropdown."
	strength_dv.errorTitle = "Invalid Strength"
	strength_dv.prompt = "Select Strength (0-10) from the list"
	strength_dv.promptTitle = "Strength"
	ws.add_data_validation(strength_dv)
	strength_dv.add(f"H2:H{last_data_row}")

	# Column 9 (I): Taste - reference $U$2:$U${numeric_last_row}
	taste_range = f"$U$2:$U${numeric_last_row}"
	taste_dv = openpyxl.worksheet.datavalidation.DataValidation(
		type="list",
		formula1=taste_range,
		allow_blank=True,
	)
	taste_dv.error = "Please select a valid Taste value from the dropdown."
	taste_dv.errorTitle = "Invalid Taste"
	taste_dv.prompt = "Select Taste (0-10) from the list"
	taste_dv.promptTitle = "Taste"
	ws.add_data_validation(taste_dv)
	taste_dv.add(f"I2:I{last_data_row}")

	# Column 10 (J): Briskness - reference $V$2:$V${numeric_last_row}
	briskness_range = f"$V$2:$V${numeric_last_row}"
	briskness_dv = openpyxl.worksheet.datavalidation.DataValidation(
		type="list",
		formula1=briskness_range,
		allow_blank=True,
	)
	briskness_dv.error = "Please select a valid Briskness value from the dropdown."
	briskness_dv.errorTitle = "Invalid Briskness"
	briskness_dv.prompt = "Select Briskness (0-10) from the list"
	briskness_dv.promptTitle = "Briskness"
	ws.add_data_validation(briskness_dv)
	briskness_dv.add(f"J2:J{last_data_row}")

	# Save to BytesIO
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	# Encode to base64 for safe JSON transport
	encoded = base64.b64encode(output.getvalue()).decode("utf-8")

	return {"content": encoded, "filename": "tea_evaluation_import.xlsx"}
