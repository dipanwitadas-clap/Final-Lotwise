# # Copyright (c) 2026, BusinessThat.Works and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class TeaLotImport(Document):
# 	# begin: auto-generated types
# 	# This code is auto-generated. Do not modify anything in this block.

# 	from typing import TYPE_CHECKING

# 	if TYPE_CHECKING:
# 		from frappe.types import DF


# 	# end: auto-generated types

# 	_DOCTYPE_NAME = "Tea Lot Import"
# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt
"""Tea Lot Import — staging doctype that parses an agent's auction-style
purchase list (Excel) and creates one Tea Lot per line item.

Design notes
------------
* Column positions are NOT stable across agents/centres, so the parser locates
  columns by matching the header row's labels against a synonym list
  (`COLUMN_SYNONYMS`) rather than by fixed cell position. Add new label variants
  to that list instead of changing code.
* Header metadata (Sale No, Centre, Date, Blend, Company) is found the same way,
  by searching for label cells and reading the value to the right or below.
* Parsing creates nothing; `create_tea_lots` does the writes, per-row, so one bad
  row never aborts the batch. Re-running errors on already-imported rows (dedup).

Master-resolution assumes the masters are auto-named by their primary field
(Estate -> estate_name, Mark -> mark_name, Grade -> grade_code), so that the
record `name` equals the text on the sheet. If those doctypes use a different
naming rule, adjust `_ensure_*` accordingly.
"""

import re

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

# --------------------------------------------------------------------------- config

# Field -> list of accepted header labels (will be normalised before comparison).
COLUMN_SYNONYMS = {
	"lot_no": ["lot no", "lot number", "lot"],
	"invoice_number": ["invoice no", "invoice number", "invoice", "inv no"],
	"mark_raw": ["garden mark", "garden", "mark"],
	"grade_raw": ["grade"],
	"packages": ["no of pkgs", "no of packages", "pkgs", "packages", "no pkgs"],
	"gross_wtpkg": ["wt kgs", "wt kg", "gross wt", "wt"],
	"net_weight_total": ["nett wt kg", "nett wt", "net wt", "net weight", "nett weight"],
	"rate": ["rate kg", "rate kgs", "rate"],
	"density": ["density"],
	"liquor_mark": ["liquor mark", "liquor"],
	"sam_pkg": ["sam pkg", "sample pkg", "sample pkgs"],
	"sam_wt": ["sam wt", "sample wt"],
	"sample_detail": ["sample detail", "sample details"],
}

# Header metadata labels -> normalised synonyms. Value is read to the right of the
# label cell, falling back to the cell(s) below.
SALE_NO_LABELS = ["sale no", "sale number"]
CENTRE_LABELS = ["auction", "centre", "center", "auction centre"]
DATE_LABELS = ["date"]
BLEND_LABELS = ["blend type", "blend"]
COMPANY_LABELS = ["company"]

# Fields used to recognise the data header row, and the quorum required.
HEADER_QUORUM = 4
HEADER_REQUIRED_ANY = ("net_weight_total", "packages")

ALLOWED_LIQUOR = {"A+", "A", "B+", "B", "C+", "C"}

PKG_TOLERANCE = 0  # exact
WEIGHT_TOLERANCE = 1.0  # kg


# --------------------------------------------------------------------------- helpers


def _norm(value) -> str:
	"""Lower-case, strip, and collapse anything non-alphanumeric to single spaces."""
	if value is None:
		return ""
	text = str(value).strip().lower()
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return text.strip()


def _find_header(ws, scan_rows: int = 60):
	"""Return (header_row_index, {field: column_index}) by matching labels.

	Scans the top `scan_rows` rows; the header is the first row whose cells match
	at least HEADER_QUORUM distinct fields and include lot_no plus a quantity column.
	Column indices are 1-based (openpyxl convention).
	"""
	max_row = min(ws.max_row, scan_rows)
	for r in range(1, max_row + 1):
		colmap = {}
		for c in range(1, ws.max_column + 1):
			norm = _norm(ws.cell(r, c).value)
			if not norm:
				continue
			for field, syns in COLUMN_SYNONYMS.items():
				if field in colmap:
					continue
				if norm in syns:
					colmap[field] = c
					break
		if (
			len(colmap) >= HEADER_QUORUM
			and "lot_no" in colmap
			and any(f in colmap for f in HEADER_REQUIRED_ANY)
		):
			return r, colmap
	return None, {}


# Every known label (column + metadata) — a metadata *value* should never be one
# of these, so candidates matching this set are skipped during value lookup.
_ALL_LABELS = set()
for _syns in COLUMN_SYNONYMS.values():
	_ALL_LABELS.update(_syns)
for _syns in (SALE_NO_LABELS, CENTRE_LABELS, DATE_LABELS, BLEND_LABELS, COMPANY_LABELS):
	_ALL_LABELS.update(_syns)


def _is_value_like(value) -> bool:
	"""A real metadata value: non-empty, not itself a label, not a totals/title cell."""
	if value in (None, ""):
		return False
	norm = _norm(value)
	if not norm or norm in _ALL_LABELS:
		return False
	if any(tok in norm for tok in ("total", "quantity", "detail", "purchase details")):
		return False
	return True


def _label_value(ws, label_syns, scan_rows: int = 60):
	"""Find a label cell (exact match) and return its value.

	The header block mixes 'value to the right' (Date, Blend) and 'value below'
	(Sale No, Auction/Centre, Company), so we test the immediate right neighbours
	then the cells directly below, skipping anything that is itself a label or a
	totals/title cell.
	"""
	max_row = min(ws.max_row, scan_rows)
	for r in range(1, max_row + 1):
		for c in range(1, ws.max_column + 1):
			if _norm(ws.cell(r, c).value) not in label_syns:
				continue
			candidates = [
				ws.cell(r, c + 1).value,
				ws.cell(r, c + 2).value if c + 2 <= ws.max_column else None,
			]
			for rr in range(r + 1, min(r + 3, ws.max_row) + 1):
				candidates.append(ws.cell(rr, c).value)
			for cand in candidates:
				if _is_value_like(cand):
					return cand
	return None


def _cell(ws, r, colmap, field):
	col = colmap.get(field)
	return ws.cell(r, col).value if col else None


def _read_rows(ws, header_row, colmap):
	"""Read data rows beneath the header until a totals/blank sentinel.

	Returns (rows, totals) where rows is a list of dicts and totals carries the
	sheet's PAGE TOTAL packages/net weight (read at the mapped columns).
	"""
	rows = []
	totals = {"packages": None, "net_weight_total": None}
	for r in range(header_row + 1, ws.max_row + 1):
		all_cells = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
		if any("total" in _norm(c) for c in all_cells):
			totals["packages"] = _cell(ws, r, colmap, "packages")
			totals["net_weight_total"] = _cell(ws, r, colmap, "net_weight_total")
			break

		lot_no = _cell(ws, r, colmap, "lot_no")
		mark = _cell(ws, r, colmap, "mark_raw")
		if (lot_no in (None, "")) and (mark in (None, "")):
			continue  # blank / spacer / stray-column row

		rows.append(
			{
				"lot_no": _str(lot_no),
				"invoice_number": _str(_cell(ws, r, colmap, "invoice_number")),
				"mark_raw": _str(mark),
				"grade_raw": _str(_cell(ws, r, colmap, "grade_raw")),
				"packages": cint(_cell(ws, r, colmap, "packages")),
				"gross_wtpkg": flt(_cell(ws, r, colmap, "gross_wtpkg")),
				"net_weight_total": flt(_cell(ws, r, colmap, "net_weight_total")),
				"rate": flt(_cell(ws, r, colmap, "rate")),
				"density": flt(_cell(ws, r, colmap, "density")),
				"liquor_mark": _str(_cell(ws, r, colmap, "liquor_mark")),
				"sam_pkg": _str(_cell(ws, r, colmap, "sam_pkg")),
				"sam_wt": _str(_cell(ws, r, colmap, "sam_wt")),
				"sample_detail": _str(_cell(ws, r, colmap, "sample_detail")),
				"row_status": "Pending",
			}
		)
	return rows, totals


def _str(value):
	if value is None:
		return None
	return str(value).strip()


# --------------------------------------------------------------------------- doctype


class TeaLotImport(Document):
	# ---- actions (called from the form) ----

	@frappe.whitelist()
	def parse_file(self):
		"""Read the attached workbook into the items table. Creates no Tea Lots."""
		ws = self._load_sheet()

		# header metadata (don't overwrite a value the user already set)
		self.sale_no = self.sale_no or _str(_label_value(ws, SALE_NO_LABELS))
		self.centre = self.centre or _str(_label_value(ws, CENTRE_LABELS))
		self.blend = self.blend or _str(_label_value(ws, BLEND_LABELS))
		self.company = self.company or _str(_label_value(ws, COMPANY_LABELS))
		if not self.purchase_date:
			d = _label_value(ws, DATE_LABELS)
			if d:
				try:
					self.purchase_date = getdate(d)
				except Exception:
					pass
		if not self.acquisition_channel:
			self.acquisition_channel = "Auction"

		header_row, colmap = _find_header(ws)
		if not header_row:
			frappe.throw(
				_(
					"Could not locate the column header row. Check the sheet, or add the "
					"missing label to COLUMN_SYNONYMS."
				)
			)

		rows, totals = _read_rows(ws, header_row, colmap)

		self.set("items", [])
		for row in rows:
			self.append("items", row)

		# reconciliation
		self.computed_total_packages = sum(cint(r["packages"]) for r in rows)
		self.computed_total_net_weight = sum(flt(r["net_weight_total"]) for r in rows)
		self.parsed_total_packages = cint(totals.get("packages"))
		self.parsed_total_net_weight = flt(totals.get("net_weight_total"))
		self.reconciled = int(
			self.parsed_total_packages
			and abs(self.parsed_total_packages - self.computed_total_packages) <= PKG_TOLERANCE
			and abs(self.parsed_total_net_weight - self.computed_total_net_weight) <= WEIGHT_TOLERANCE
		)

		self.rows_parsed = len(rows)
		self.rows_created = 0
		self.rows_error = 0
		self.rows_duplicate = 0
		self.save()

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
		"""Create a Tea Lot for each pending row. Per-row, fault-isolated, idempotent."""
		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.items:
			if row.row_status == "Created":
				continue
			try:
				mark_name = (row.mark_raw or "").strip()
				invoice = (row.invoice_number or "").strip()
				lot_no = (row.lot_no or "").strip()

				if not mark_name or not invoice:
					row.row_status = "Error"
					row.message = _("Missing Mark or Invoice Number.")
					error += 1
					continue

				liquor = (row.liquor_mark or "").strip()
				if liquor and liquor not in ALLOWED_LIQUOR:
					row.row_status = "Error"
					row.message = _("Invalid Liquor Mark: {0}").format(liquor)
					error += 1
					continue

				if self._is_duplicate(lot_no, mark_name, meta):
					row.row_status = "Duplicate"
					row.message = _("A Tea Lot with this Year + Lot No + Mark already exists.")
					duplicate += 1
					continue

				notes = []
				self._ensure_estate_and_mark(mark_name, notes)
				grade_code = (row.grade_raw or "").strip()
				if grade_code:
					self._ensure_grade(grade_code, notes)

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
				}
				# only keep fields that actually exist on Tea Lot (schema-drift safe)
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				lot = frappe.get_doc(values)
				lot.insert(ignore_permissions=True)

				row.tea_lot = lot.name
				row.row_status = "Created"
				row.created_masters = ", ".join(notes)
				row.message = _("Created {0}").format(lot.name)
				created += 1
			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Tea Lot Import: row failed")

		self.rows_created = created
		self.rows_error = error
		self.rows_duplicate = duplicate
		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}

	# ---- internals ----

	def _load_sheet(self):
		if not self.import_file:
			frappe.throw(_("Attach an import file first."))
		file_doc = frappe.get_doc("File", {"file_url": self.import_file})
		wb = openpyxl.load_workbook(file_doc.get_full_path(), data_only=True)
		if self.sheet_name:
			if self.sheet_name not in wb.sheetnames:
				frappe.throw(
					_("Sheet '{0}' not found. Available: {1}").format(
						self.sheet_name, ", ".join(wb.sheetnames)
					)
				)
			return wb[self.sheet_name]
		return wb[wb.sheetnames[0]]

	def _is_duplicate(self, lot_no, mark_name, meta):
		if not lot_no:
			return False
		fields = ["name"]
		has_pd = meta.has_field("purchase_date")
		if has_pd:
			fields.append("purchase_date")
		existing = frappe.get_all("Tea Lot", filters={"lot_no": lot_no, "mark": mark_name}, fields=fields)
		if not existing:
			return False
		if has_pd and self.purchase_date:
			year = getdate(self.purchase_date).year
			return any(e.get("purchase_date") and getdate(e["purchase_date"]).year == year for e in existing)
		# no date to disambiguate on — any lot_no + mark match counts
		return True

	def _ensure_estate_and_mark(self, mark_name, notes):
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
		if not frappe.db.exists("Grade", grade_code):
			frappe.get_doc({"doctype": "Grade", "grade_code": grade_code}).insert(ignore_permissions=True)
			notes.append(_("Grade '{0}'").format(grade_code))
