# # # Copyright (c) 2026, BusinessThat.Works and contributors
# # # For license information, please see license.txt
import re

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

# --------------------------------------------------------------------------- config
# Add new column
HEADER_TO_FIELD = {
	"lot no": {"field": "lot_no", "type": "str", "required": True},
	"invoice no": {"field": "invoice_number", "type": "str"},
	"garden mark": {"field": "mark_raw", "type": "str", "required": True},
	"grade": {"field": "grade_raw", "type": "str", "required": True},
	"region qualifier": {"field": "grade_qualifier", "type": "str"},
	"no of pkgs": {"field": "packages", "type": "int", "required": True},
	"wt kgs": {"field": "gross_wtpkg", "type": "float"},
	"nett wt kgs": {"field": "net_weight_total", "type": "float", "required": True},
	"rate kg": {"field": "rate", "type": "float"},
	"liquor mark": {"field": "liquor_mark", "type": "str"},
	"density": {"field": "density", "type": "float"},
	"bill mode": {"field": "bill_mode", "type": "str"},
	"sample pkgs": {"field": "sam_pkg", "type": "str"},
	"sample wt": {"field": "sam_wt", "type": "str"},
	"remarks": {"field": "remarks", "type": "str"},
	"purchase from": {"field": "purchase_from", "type": "str"},
	"purchase invoice no": {"field": "purchase_invoice_no", "type": "str"},
	"purchase invoice date": {"field": "purchase_invoice_date", "type": "str"},
	"warehouse name": {"field": "warehouse_name", "type": "str"},
	"total amount as per to tax invoice": {"field": "total_amount_as_per_to_tax_invoice", "type": "float"},
}


# --------------------------------------------------------------------------- helpers


def _norm(value) -> str:
	"""Lowercase, strip, replace non-alphanum with single space."""
	if value is None:
		return ""
	return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def _str(value):
	"""Convert to stripped string, return None if empty."""
	return None if value is None else str(value).strip()


def _get_liquor_options():
	"""Fetch valid liquor marks from Tea Lot doctype field (dynamic)."""
	field = frappe.get_meta("Tea Lot").get_field("liquor_mark")
	if not field or not field.options:
		return set()
	return {o.strip() for o in field.options.strip().split("\n") if o.strip()}


def _detect_columns(ws, header_row=13):
	"""Match Excel column headers to field configs. Throw if required columns missing."""
	colmap = {}
	found = set()
	for col in range(1, ws.max_column + 1):
		val = ws.cell(header_row, col).value
		if not val:
			continue
		key = _norm(val)
		if key in HEADER_TO_FIELD:
			colmap[col] = HEADER_TO_FIELD[key]
			found.add(key)
	missing = [h for h, c in HEADER_TO_FIELD.items() if c.get("required") and h not in found]
	if missing:
		frappe.throw(
			_("Missing required column(s): {0}. Check the template.").format(
				", ".join(h.title() for h in missing)
			)
		)
	return colmap


def _extract_metadata(ws):
	"""Read header block from Dalmia template (rows 4-10, col B)."""
	meta = {}
	meta["acquisition_channel"] = _str(ws.cell(4, 2).value) or "Auction"
	meta["company"] = _str(ws.cell(5, 2).value)
	date_val = ws.cell(6, 2).value
	meta["purchase_date"] = getdate(date_val) if date_val else None
	meta["blend"] = _str(ws.cell(7, 2).value)
	meta["reference_no"] = _str(ws.cell(8, 2).value)
	meta["centre"] = _str(ws.cell(9, 2).value)
	meta["sale_no"] = _str(ws.cell(10, 2).value)
	return meta


def _convert_cell(value, field_type):
	"""Cast cell value to int/float/str based on field type."""
	if field_type == "int":
		return cint(value) if value else 0
	if field_type == "float":
		return flt(value) if value else 0.0
	return _str(value)


def _read_data_rows(ws, colmap, start_row=15):
	"""Iterate data rows, return list of row dicts."""
	rows = []
	for row in range(start_row, ws.max_row + 1):
		if not any(ws.cell(row, c).value is not None for c in colmap):
			break
		row_dict = {"row_status": "Pending"}
		has_data = False
		for col, cfg in colmap.items():
			val = _convert_cell(ws.cell(row, col).value, cfg["type"])
			row_dict[cfg["field"]] = val
			if cfg.get("required") and val:
				has_data = True
		if has_data:
			rows.append(row_dict)
	return rows


# --------------------------------------------------------------------------- doctype


class TeaLotImport(Document):
	"""Parse Dalmia XLSX -> items table -> create Tea Lots."""

	@frappe.whitelist()
	def parse_file(self):
		"""Parse XLSX, populate items table, compute totals."""
		ws = self._load_sheet()
		colmap = _detect_columns(ws)
		meta = _extract_metadata(ws)
		self.acquisition_channel = meta.get("acquisition_channel", "Auction")
		self.company = meta.get("company")
		self.purchase_date = meta.get("purchase_date")
		self.blend = meta.get("blend")
		self.centre = meta.get("centre")
		self.sale_no = meta.get("sale_no")

		rows = _read_data_rows(ws, colmap)

		self.set("items", [])
		for row in rows:
			self.append("items", row)

		self.computed_total_packages = sum(cint(r.get("packages", 0)) for r in rows)
		self.computed_total_net_weight = sum(flt(r.get("net_weight_total", 0)) for r in rows)
		self.rows_parsed = len(rows)
		self.rows_created = 0
		self.rows_error = 0
		self.rows_duplicate = 0
		self.save()

		return {"rows": len(rows)}

	@frappe.whitelist()
	def create_tea_lots(self):
		"""Create Tea Lot for each Pending row. Validates, dedupes, creates masters."""
		meta = frappe.get_meta("Tea Lot")
		allowed_liquor = _get_liquor_options()
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
				if liquor and allowed_liquor and liquor not in allowed_liquor:
					row.row_status = "Error"
					row.message = _("Invalid Liquor Mark: {0}").format(liquor)
					error += 1
					continue

				if self._is_duplicate(lot_no, mark_name, meta):
					row.row_status = "Duplicate"
					row.message = _("Duplicate Year + Lot No + Mark.")
					duplicate += 1
					continue

				grade_code = (row.grade_raw or "").strip()

				if not frappe.db.exists("Mark", mark_name):
					row.row_status = "Error"
					row.message = _("Mark '{0}' not found. Please create it first.").format(mark_name)
					error += 1
					continue

				if grade_code and not frappe.db.exists("Grade", grade_code):
					row.row_status = "Error"
					row.message = _("Grade '{0}' not found. Please create it first.").format(grade_code)
					error += 1
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": self.acquisition_channel or "Auction",
					"status": "Offered",
					"holding_status": "Committed",
					"lot_no": lot_no,
					"invoice_number": invoice,
					"mark": mark_name,
					"grade": grade_code or None,
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
					"purchase_from": row.purchase_from,
					"purchase_invoice_no": row.purchase_invoice_no,
					"purchase_invoice_date": row.purchase_invoice_date,
					"warehouse_name": row.warehouse_name,
					"total_amount_as_per_to_tax_invoice": flt(row.total_amount_as_per_to_tax_invoice),
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				lot = frappe.get_doc(values)
				lot.insert(ignore_permissions=True)

				row.tea_lot = lot.name
				row.row_status = "Created"
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
		"""Open attached XLSX, return 'Purchase List' worksheet."""
		if not self.import_file:
			frappe.throw(_("Attach an import file first."))
		file_doc = frappe.get_doc("File", {"file_url": self.import_file})
		wb = openpyxl.load_workbook(file_doc.get_full_path(), data_only=True)
		if "Purchase List" not in wb.sheetnames:
			frappe.throw(_("Sheet 'Purchase List' not found."))
		return wb["Purchase List"]

	def _is_duplicate(self, lot_no, mark_name, meta):
		"""Check if lot_no + mark already exists (same year if purchase_date set)."""
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
		return True
