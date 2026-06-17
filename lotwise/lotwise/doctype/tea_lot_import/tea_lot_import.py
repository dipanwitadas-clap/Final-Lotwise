# # # Copyright (c) 2026, BusinessThat.Works and contributors
# # # For license information, please see license.txt
import re

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

# --------------------------------------------------------------------------- config

# Expected columns in the Dalmia template (row 13), mapped to field names
# KEYS ARE NORMALIZED VERSIONS (all punctuation removed, lowercased)
DALMIA_COLUMN_MAP = {
	1: "lot_no",
	2: "invoice_number",
	3: "mark_raw",
	4: "grade_raw",
	5: "grade_qualifier",
	6: "packages",
	7: "gross_wtpkg",
	8: "net_weight_total",
	9: "rate",
	10: "liquor_mark",
	11: "density",
	12: "bill_mode",
	13: "sam_pkg",
	14: "sam_wt",
	15: "remarks",
}

# Expected column headers (NORMALIZED - all non-alphanumeric removed)
# These keys match what comes out of _norm() function
# ✅ FIXED: All keys are now properly normalized to match the _norm() function output
EXPECTED_HEADERS = {
	"lot no": "lot_no",
	"invoice no": "invoice_number",
	"garden mark": "mark_raw",  # ✅ FIXED: was "garden / mark"
	"grade": "grade_raw",
	"region qualifier": "grade_qualifier",
	"no of pkgs": "packages",
	"wt kgs": "gross_wtpkg",  # ✅ FIXED: was "wt (kgs)"
	"nett wt kgs": "net_weight_total",  # ✅ FIXED: was "nett. wt. (kgs.)"
	"rate kg": "rate",  # ✅ FIXED: was "rate / kg"
	"liquor mark": "liquor_mark",
	"density": "density",
	"bill mode": "bill_mode",
	"sample pkgs": "sam_pkg",
	"sample wt": "sam_wt",
	"remarks": "remarks",
}

# Allowed liquor marks for validation
ALLOWED_LIQUOR = {"A+", "A", "B+", "B", "C+", "C"}

# Tolerance values for reconciliation
PKG_TOLERANCE = 0  # exact match required
WEIGHT_TOLERANCE = 1.0  # kg tolerance


# --------------------------------------------------------------------------- helpers


def _norm(value) -> str:
	"""Lower-case, strip, and collapse anything non-alphanumeric to single spaces.

	Examples:
	- "Garden / Mark *" → "garden mark"
	- "Nett. Wt. (Kgs.) *" → "nett wt kgs"
	- "Wt (Kgs.)" → "wt kgs"
	- "Rate / Kg." → "rate kg"
	"""
	if value is None:
		return ""
	text = str(value).strip().lower()
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return text.strip()


def _str(value):
	"""Convert to string, strip whitespace. Return None if empty."""
	if value is None:
		return None
	return str(value).strip()


def _validate_dalmia_header(ws):
	"""Validate that row 13 contains the expected Dalmia headers.

	Reads row 13, normalizes each column header, and matches against EXPECTED_HEADERS.

	Args:
		ws: openpyxl worksheet object

	Returns:
		dict mapping column_index (1-15) -> field_name if valid

	Raises:
		frappe.ValidationError if critical columns missing
	"""
	colmap = {}
	for col in range(1, 16):
		cell_value = ws.cell(13, col).value
		if not cell_value:
			continue
		norm = _norm(cell_value)
		field = EXPECTED_HEADERS.get(norm)
		if field:
			colmap[col] = field

	# Validate we have the critical fields
	if not any(f == "lot_no" for f in colmap.values()):
		frappe.throw(_("Column header row 13 is missing 'Lot No'. Check the template."))
	if not any(f in ("packages", "net_weight_total") for f in colmap.values()):
		frappe.throw(
			_("Column header row 13 is missing 'No of Pkgs' or 'Nett. Wt. (Kgs.)'. Check the template.")
		)

	return colmap


def _extract_metadata(ws):
	"""Extract the header metadata block (rows 4-10, column B).

	Reads fixed positions:
	- Row 4, Col B: Acquisition Channel (Auction/Private/Outsourced)
	- Row 5, Col B: Company
	- Row 6, Col B: Purchase Date
	- Row 7, Col B: Blend / Brand
	- Row 8, Col B: Reference No
	- Row 9, Col B: Auction Centre
	- Row 10, Col B: Sale No

	Args:
		ws: openpyxl worksheet object

	Returns:
		dict with keys: acquisition_channel, company, purchase_date, blend,
		               reference_no, centre, sale_no
	"""
	metadata = {}

	# Row 4: Channel (Acquisition Channel)
	metadata["acquisition_channel"] = _str(ws.cell(4, 2).value) or "Auction"

	# Row 5: Company
	metadata["company"] = _str(ws.cell(5, 2).value)

	# Row 6: Purchase Date
	date_val = ws.cell(6, 2).value
	if date_val:
		try:
			metadata["purchase_date"] = getdate(date_val)
		except Exception:
			metadata["purchase_date"] = None
	else:
		metadata["purchase_date"] = None

	# Row 7: Blend / Brand
	metadata["blend"] = _str(ws.cell(7, 2).value)

	# Row 8: Reference No
	metadata["reference_no"] = _str(ws.cell(8, 2).value)

	# Row 9: Auction Centre
	metadata["centre"] = _str(ws.cell(9, 2).value)

	# Row 10: Sale No
	metadata["sale_no"] = _str(ws.cell(10, 2).value)

	return metadata


def _read_data_rows(ws, colmap):
	"""Read data rows (starting row 15 onwards).

	Iterates from row 15 until a completely blank row or totals row is found.
	For each row, extracts all 15 columns using the column mapping.

	Args:
		ws: openpyxl worksheet object
		colmap: dict mapping column_index -> field_name

	Returns:
		tuple: (rows, totals)
		- rows: list of dicts, one per data row
		- totals: dict with 'packages' and 'net_weight_total' from TOTAL row if found
	"""
	rows = []
	totals = {"packages": None, "net_weight_total": None}

	for row in range(15, ws.max_row + 1):
		# Check if this is a totals/blank row
		all_cells = [ws.cell(row, c).value for c in range(1, 16)]
		if all(c in (None, "") for c in all_cells):
			break  # Stop at first completely blank row
		if any("total" in _norm(str(c)) for c in all_cells if c):
			# Found totals row; extract totals and stop
			for col, field in colmap.items():
				if field == "packages":
					totals["packages"] = cint(ws.cell(row, col).value)
				elif field == "net_weight_total":
					totals["net_weight_total"] = flt(ws.cell(row, col).value)
			break

		# Extract lot_no and mark to check if row is empty
		lot_no = None
		mark = None
		for col, field in colmap.items():
			if field == "lot_no":
				lot_no = _str(ws.cell(row, col).value)
			elif field == "mark_raw":
				mark = _str(ws.cell(row, col).value)

		if not lot_no and not mark:
			continue  # Skip blank/spacer rows

		# Build row dict with all 15 fields
		row_dict = {"row_status": "Pending"}
		for col, field in colmap.items():
			cell_value = ws.cell(row, col).value
			if field == "lot_no":
				row_dict["lot_no"] = _str(cell_value)
			elif field == "invoice_number":
				row_dict["invoice_number"] = _str(cell_value)
			elif field == "mark_raw":
				row_dict["mark_raw"] = _str(cell_value)
			elif field == "grade_raw":
				row_dict["grade_raw"] = _str(cell_value)
			elif field == "grade_qualifier":
				row_dict["grade_qualifier"] = _str(cell_value)
			elif field == "packages":
				row_dict["packages"] = cint(cell_value) if cell_value else 0
			elif field == "gross_wtpkg":
				row_dict["gross_wtpkg"] = flt(cell_value) if cell_value else 0.0
			elif field == "net_weight_total":
				row_dict["net_weight_total"] = flt(cell_value) if cell_value else 0.0
			elif field == "rate":
				row_dict["rate"] = flt(cell_value) if cell_value else 0.0
			elif field == "liquor_mark":
				row_dict["liquor_mark"] = _str(cell_value)
			elif field == "density":
				row_dict["density"] = flt(cell_value) if cell_value else 0.0
			elif field == "bill_mode":
				row_dict["bill_mode"] = _str(cell_value)
			elif field == "sam_pkg":
				row_dict["sam_pkg"] = _str(cell_value)
			elif field == "sam_wt":
				row_dict["sam_wt"] = _str(cell_value)
			elif field == "remarks":
				row_dict["remarks"] = _str(cell_value)

		rows.append(row_dict)

	return rows, totals


# --------------------------------------------------------------------------- doctype


class TeaLotImport(Document):
	"""Tea Lot Import doctype - parses Dalmia purchase list XLSX and creates Tea Lots.

	Public Methods (called from UI buttons):
	- parse_file(): Reads XLSX, validates structure, populates child table
	- create_tea_lots(): Creates Tea Lot records from parsed data

	Private Methods:
	- _load_sheet(): Opens the XLSX file
	- _is_duplicate(): Checks if lot already exists
	- _ensure_estate_and_mark(): Auto-creates Estate and Mark if needed
	- _ensure_grade(): Auto-creates Grade if needed
	"""

	# ---- actions (called from the form) ----

	@frappe.whitelist()
	def parse_file(self):
		"""Read the attached Dalmia workbook into the items table. Creates no Tea Lots.

		Flow:
		1. Load and open the XLSX file
		2. Validate header row (row 13) has all expected columns
		3. Extract metadata from rows 4-10 column B
		4. Read data rows (15+) with all 15 columns
		5. Populate child table with parsed rows
		6. Calculate reconciliation totals
		7. Show summary and any warnings

		Returns:
			dict: {"rows": count, "reconciled": boolean}
		"""
		ws = self._load_sheet()

		# Validate header - ensure all columns present
		colmap = _validate_dalmia_header(ws)

		# Extract metadata from fixed positions
		metadata = _extract_metadata(ws)
		self.acquisition_channel = metadata.get("acquisition_channel", "Auction")
		self.company = metadata.get("company")
		self.purchase_date = metadata.get("purchase_date")
		self.blend = metadata.get("blend")
		self.centre = metadata.get("centre")
		self.sale_no = metadata.get("sale_no")

		# Read all data rows
		rows, totals = _read_data_rows(ws, colmap)

		# Update items table - clear old and add new rows
		self.set("items", [])
		for row in rows:
			self.append("items", row)

		# Reconciliation - compare computed totals with sheet totals
		self.computed_total_packages = sum(cint(r.get("packages", 0)) for r in rows)
		self.computed_total_net_weight = sum(flt(r.get("net_weight_total", 0)) for r in rows)
		self.parsed_total_packages = cint(totals.get("packages"))
		self.parsed_total_net_weight = flt(totals.get("net_weight_total"))

		self.reconciled = int(
			self.parsed_total_packages
			and abs(self.parsed_total_packages - self.computed_total_packages) <= PKG_TOLERANCE
			and abs(self.parsed_total_net_weight - self.computed_total_net_weight) <= WEIGHT_TOLERANCE
		)

		# Update summary
		self.rows_parsed = len(rows)
		self.rows_created = 0
		self.rows_error = 0
		self.rows_duplicate = 0
		self.save()

		# Warn if totals don't match
		if self.parsed_total_packages and not self.reconciled:
			frappe.msgprint(
				_(
					"Parsed {0} rows, but totals do not reconcile with the sheet's PAGE TOTAL "
					"({1} pkgs / {2} kg vs {3} pkgs / {4} kg). Please review before creating."
				).format(
					len(rows),
					self.computed_total_packages,
					self.computed_total_net_weight,
					self.parsed_total_packages,
					self.parsed_total_net_weight,
				),
				indicator="orange",
			)
		return {"rows": len(rows), "reconciled": self.reconciled}

	@frappe.whitelist()
	def create_tea_lots(self):
		"""Create a Tea Lot for each pending row. Per-row, fault-isolated, idempotent.

		For each row in the child table with status "Pending":
		1. Validate required fields (Mark, Invoice)
		2. Validate liquor mark format
		3. Check for duplicates
		4. Auto-create Estate, Mark, Grade if needed
		5. Create Tea Lot record
		6. Mark row as Created/Error/Duplicate

		Returns:
			dict: {"created": count, "errors": count, "duplicates": count}
		"""
		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.items:
			# Skip already created rows
			if row.row_status == "Created":
				continue
			try:
				# Extract key fields
				mark_name = (row.mark_raw or "").strip()
				invoice = (row.invoice_number or "").strip()
				lot_no = (row.lot_no or "").strip()

				# Validation 1: Required fields
				if not mark_name or not invoice:
					row.row_status = "Error"
					row.message = _("Missing Mark or Invoice Number.")
					error += 1
					continue

				# Validation 2: Liquor mark format
				liquor = (row.liquor_mark or "").strip()
				if liquor and liquor not in ALLOWED_LIQUOR:
					row.row_status = "Error"
					row.message = _("Invalid Liquor Mark: {0}").format(liquor)
					error += 1
					continue

				# Validation 3: Check for duplicates
				if self._is_duplicate(lot_no, mark_name, meta):
					row.row_status = "Duplicate"
					row.message = _("A Tea Lot with this Year + Lot No + Mark already exists.")
					duplicate += 1
					continue

				# Auto-create masters if needed
				notes = []
				self._ensure_estate_and_mark(mark_name, notes)
				grade_code = (row.grade_raw or "").strip()
				if grade_code:
					self._ensure_grade(grade_code, notes)

				# Build Tea Lot values
				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": self.acquisition_channel or "Auction",
					"status": "Offered",
					"lot_no": lot_no,
					"invoice_number": invoice,
					"mark": mark_name,
					"grade": grade_code or None,
					"packing": "PS",
					"packages": cint(row.packages),
					"gross_wtpkg": flt(row.gross_wtpkg),
					"net_weight_total": flt(row.net_weight_total),
					"rate": flt(row.rate),
					"density": flt(row.density),
					"liquor_mark": liquor or None,
					"blend": self.blend or None,
					"sale_no": self.sale_no or None,
					"centre": self.centre or None,
					"purchase_date": self.purchase_date or None,
					"source_doctype": self.doctype or None,
					"source_doctype_id": self.name or None,
				}
				# Only keep fields that exist on Tea Lot (schema-drift safe)
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				# Create and save Tea Lot
				lot = frappe.get_doc(values)
				lot.insert(ignore_permissions=True)

				# Update row with success
				row.tea_lot = lot.name
				row.row_status = "Created"
				row.created_masters = ", ".join(notes)
				row.message = _("Created {0}").format(lot.name)
				created += 1
			except Exception as e:
				# Mark row as error
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Tea Lot Import: row failed")

		# Update parent summary
		self.rows_created = created
		self.rows_error = error
		self.rows_duplicate = duplicate
		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}

	# ---- internals ----

	def _load_sheet(self):
		"""Load and return the XLSX worksheet.

		Raises:
			frappe.ValidationError if file not attached or "Purchase List" sheet missing
		"""
		if not self.import_file:
			frappe.throw(_("Attach an import file first."))
		file_doc = frappe.get_doc("File", {"file_url": self.import_file})
		wb = openpyxl.load_workbook(file_doc.get_full_path(), data_only=True)
		# Always use "Purchase List" sheet from Dalmia template
		if "Purchase List" not in wb.sheetnames:
			frappe.throw(_("Sheet 'Purchase List' not found. Ensure you're using the Dalmia template."))
		return wb["Purchase List"]

	def _is_duplicate(self, lot_no, mark_name, meta):
		"""Check if a Tea Lot with this lot_no + mark + year already exists.

		Args:
			lot_no: Lot number to check
			mark_name: Mark name to check
			meta: DocType metadata for Tea Lot

		Returns:
			boolean: True if duplicate found
		"""
		if not lot_no:
			return False
		fields = ["name"]
		has_pd = meta.has_field("purchase_date")
		if has_pd:
			fields.append("purchase_date")
		existing = frappe.get_all("Tea Lot", filters={"lot_no": lot_no, "mark": mark_name}, fields=fields)
		if not existing:
			return False
		# If purchase date available, only match same year
		if has_pd and self.purchase_date:
			year = getdate(self.purchase_date).year
			return any(e.get("purchase_date") and getdate(e["purchase_date"]).year == year for e in existing)
		# Without date to disambiguate, any lot_no + mark match counts as duplicate
		return True

	def _ensure_estate_and_mark(self, mark_name, notes):
		"""Auto-create Estate and Mark if they don't exist.

		Creates Estate (if missing) and Mark (if missing), both named after mark_name.

		Args:
			mark_name: Name to use for Estate and Mark
			notes: List to append creation notes to
		"""
		if frappe.db.exists("Mark", mark_name):
			return
		if not frappe.db.exists("Estate", mark_name):
			frappe.get_doc({"doctype": "Estate", "estate_name": mark_name}).insert(ignore_permissions=True)
			notes.append(_("Estate '{0}'").format(mark_name))
		frappe.get_doc({"doctype": "Mark", "mark_name": mark_name, "estate": mark_name}).insert(
			ignore_permissions=True
		)
		notes.append(_("Mark '{0}'").format(mark_name))

	def _ensure_grade(self, grade_code, notes):
		"""Auto-create Grade if it doesn't exist.

		Args:
			grade_code: Grade code to create
			notes: List to append creation notes to
		"""
		if not frappe.db.exists("Grade", grade_code):
			frappe.get_doc({"doctype": "Grade", "grade_code": grade_code}).insert(ignore_permissions=True)
			notes.append(_("Grade '{0}'").format(grade_code))
