# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import re
import xml.etree.ElementTree as ET
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, flt

# --------------------------------------------------------------------------- config
#
# Both weekly exports (Deal Book / Auction All Catalog) are SpreadsheetML "Excel 2003
# XML" files saved with an .xls/.xlsx-looking name - NOT real xlsx (zip) or xls
# (binary) files, so openpyxl/xlrd cannot open them. They are read with the stdlib
# xml.etree.ElementTree instead (see _read_spreadsheetml_rows). Both have a plain
# header on row 1 with no metadata block above it (unlike the Dalmia template used by
# Tea Lot Import).
#
# Only the two source files are parsed here - Tea Lot creation from Buying Week is a
# later phase and is intentionally not implemented yet.

_SS_NS = "urn:schemas-microsoft-com:office:spreadsheet"

# Deal Book columns -> shared child table fields (normalized header -> field/type)
HEADER_TO_FIELD_DEAL_BOOK = {
	"lotno": {"field": "lot_no", "type": "str"},
	"mark": {"field": "mark_raw", "type": "str"},
	"grade": {"field": "grade_raw", "type": "str"},
	"qty pkgs": {"field": "packages", "type": "int"},
	"invoice no": {"field": "invoice_number", "type": "str"},
	"price kg": {"field": "price_per_kg", "type": "float"},
	"auct val": {"field": "auction_valuation", "type": "float"},
	"packages wt pkg": {"field": "gross_wtpkg", "type": "float"},
	"auct code": {"field": "broker_code", "type": "str"},
	"baseprice": {"field": "base_price", "type": "float"},
	"total grosswt": {"field": "gross_weight", "type": "float"},
	"ntwt": {"field": "net_weight", "type": "float"},
	"sampleqty kgs": {"field": "sample_qty", "type": "float"},
	"short excesswt kgs": {"field": "short_excess_weight", "type": "float"},
	"total ntwt": {"field": "total_net_weight", "type": "float"},
	"type": {"field": "tea_type", "type": "str"},
	"dealno": {"field": "deal_no", "type": "str"},
	"within": {"field": "within", "type": "str"},
	"export": {"field": "export", "type": "str"},
	"interstate": {"field": "interstate", "type": "str"},
	"preference": {"field": "preference", "type": "str"},
	"deal time": {"field": "deal_time", "type": "str"},
	"sessiontype": {"field": "session_type", "type": "str"},
	"buyersexportaddresscode": {"field": "buyer_export_address_code", "type": "str"},
	"buyersinterstateaddresscode": {"field": "buyer_interstate_address_code", "type": "str"},
	"buyerswithinaddresscode": {"field": "buyer_within_address_code", "type": "str"},
}

# Auction All Catalog columns -> shared child table fields
HEADER_TO_FIELD_AUCTION_CATALOG = {
	"season": {"field": "season", "type": "int"},
	"sale no": {"field": "sale_no", "type": "int"},
	"auction date": {"field": "auction_date", "type": "date"},
	"session time": {"field": "session_time", "type": "str"},
	"lot no": {"field": "lot_no", "type": "str"},
	"auctioneer": {"field": "broker_code", "type": "str"},
	"origincode": {"field": "origin_code", "type": "str"},
	"teatypeid": {"field": "tea_type", "type": "str"},
	"subteatypeid": {"field": "sub_tea_type", "type": "str"},
	"categoryid": {"field": "category_id", "type": "str"},
	"markcode": {"field": "mark_raw", "type": "str"},
	"gradecode": {"field": "grade_raw", "type": "str"},
	"noofpacks": {"field": "packages", "type": "int"},
	"grossweight": {"field": "gross_weight", "type": "float"},
	"netweight": {"field": "net_weight", "type": "float"},
	"sampleqty": {"field": "sample_qty", "type": "float"},
	"invoiceweight": {"field": "invoice_weight", "type": "float"},
	"period of manufacture": {"field": "period_of_manufacture", "type": "str"},
	"baseprice": {"field": "base_price", "type": "float"},
	"auctioneers valuation": {"field": "auction_valuation", "type": "float"},
	"lastsoldprice": {"field": "last_sold_price", "type": "float"},
	"markpackagingcomments": {"field": "mark_packaging_comments", "type": "str"},
	"lot type": {"field": "lot_type", "type": "str"},
	"gpno": {"field": "gp_no", "type": "str"},
	"gpdate": {"field": "gp_date", "type": "date"},
	"invoiceno": {"field": "invoice_number", "type": "str"},
	"packagetype": {"field": "package_type", "type": "str"},
	"packagenos": {"field": "package_nos", "type": "str"},
	"warehouse name": {"field": "warehouse_name", "type": "str"},
}

# --------------------------------------------------------------------------- helpers


def _normalize_header(value) -> str:
	"""Lowercase, strip, collapse any run of non-alphanumeric characters to a
	single space - same normalization Tea Lot Import uses for its own headers."""
	if value is None:
		return ""
	return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def _convert_cell(value, field_type):
	"""Cast a raw cell value (str from a String cell, float from a Number cell) to
	the target field type. Blank and '-' (used by these exports for "not
	applicable") both mean "no value"."""
	if isinstance(value, str):
		value = value.strip()
		if value in ("", "-"):
			value = None

	if value is None:
		return None

	if field_type == "int":
		try:
			return cint(float(value))
		except (TypeError, ValueError):
			return None

	if field_type == "float":
		try:
			return flt(value)
		except (TypeError, ValueError):
			return None

	if field_type == "date":
		try:
			return datetime.strptime(str(value).strip(), "%d/%m/%Y").date()
		except (TypeError, ValueError):
			return None

	# str: a Number cell (e.g. GPNo, DealNo, the 0/1 flag columns) arrives here as a
	# Python float - format a whole number as "62" rather than "62.0".
	if isinstance(value, float) and value.is_integer():
		return str(int(value))
	return str(value).strip()


def _read_spreadsheetml_rows(path: str) -> list:
	"""Read a SpreadsheetML ("Excel 2003 XML") file's first worksheet into a list of
	rows, each row a list of cell values in column order (str for String cells,
	float for Number cells, None for empty cells). Neither export uses merged
	cells or sparse ss:Index attributes, so a plain positional read is enough."""
	ns = {"ss": _SS_NS}
	try:
		tree = ET.parse(path)
	except ET.ParseError:
		frappe.throw(_("Could not read the uploaded file. It must be a SpreadsheetML (Excel XML) export."))

	worksheet = tree.getroot().find("ss:Worksheet", ns)
	if worksheet is None:
		frappe.throw(_("No worksheet found in the uploaded file."))
	table = worksheet.find("ss:Table", ns)
	if table is None:
		frappe.throw(_("No data table found in the uploaded file."))

	number_type_attr = f"{{{_SS_NS}}}Type"
	rows = []
	for row_el in table.findall("ss:Row", ns):
		values = []
		for cell_el in row_el.findall("ss:Cell", ns):
			data_el = cell_el.find("ss:Data", ns)
			if data_el is None:
				values.append(None)
				continue
			text = data_el.text
			if text is not None and data_el.get(number_type_attr) == "Number":
				values.append(flt(text))
			else:
				values.append(text)
		rows.append(values)
	return rows


# --------------------------------------------------------------------------- doctype


class BuyingWeek(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.buying_week_deal_book_tea.buying_week_deal_book_tea import (
			BuyingWeekDealBookTea,
		)
		from lotwise.lotwise.doctype.buying_week_tea.buying_week_tea import BuyingWeekTea

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		company: DF.Data | None
		computed_total_net_weight: DF.Float
		computed_total_packages: DF.Int
		day: DF.Int
		deal_book_items: DF.Table[BuyingWeekDealBookTea]
		import_file: DF.Attach
		items: DF.Table[BuyingWeekTea]
		purchase_status: DF.Link | None
		rows_created: DF.Int
		rows_duplicate: DF.Int
		rows_error: DF.Int
		rows_parsed: DF.Int
		rows_updated: DF.Int
		sale_no: DF.Int
		season: DF.Int
		status: DF.Literal[
			"Draft",
			"Catalogue Loaded",
			"Deal Book Loaded",
			"Ordered",
			"Received",
			"Invoiced",
			"Paid",
			"Closed",
		]
		week_end: DF.Date | None
		week_no: DF.Int
		week_start: DF.Date | None
	# end: auto-generated types

	"""Parse a Deal Book / Auction All Catalog XML export -> items table, and
	create Tea Lots from the Auction Catalog rows once loaded."""

	def autoname(self):
		if self.acquisition_channel == "Auction":
			if not self.auction_centre:
				frappe.throw(_("Auction Centre is required to generate the Buying Week name."))

			auction_centre_code = frappe.db.get_value(
				"Auction Centre", self.auction_centre, "auction_centre_code"
			)
			if not auction_centre_code:
				frappe.throw(_("Auction Centre Code not found."))

			if not self.season:
				frappe.throw(_("Season is required to generate the Buying Week name."))

			if not self.sale_no:
				frappe.throw(_("Sale No is required to generate the Buying Week name."))

			if not self.day:
				frappe.throw(_("Day is required to generate the Buying Week name."))

			self.name = f"BW-{auction_centre_code}-{self.season}-{self.sale_no}-{self.day}"
		else:
			# Private/Outsourced naming hasn't been specified yet - fall back to a
			# safe generic series rather than guessing.
			self.name = make_autoname("BW-.YYYY.-.#####")

	@frappe.whitelist()
	def parse_auction_catalog(self):
		"""Read the attached file as an Auction All Catalog export."""
		return self._parse("Auction Catalog", HEADER_TO_FIELD_AUCTION_CATALOG, "Catalogue Loaded", "items")

	@frappe.whitelist()
	def parse_deal_book(self):
		"""Read the attached file as a Deal Book export."""
		return self._parse("Deal Book", HEADER_TO_FIELD_DEAL_BOOK, "Deal Book Loaded", "deal_book_items")

	def _parse(
		self, source_label: str, header_map: dict, status_after: str, target_field: str = "items"
	) -> dict:
		"""Shared body for parse_auction_catalog/parse_deal_book: read the attached
		file with `header_map`, replace the `target_field` child table (`items` for
		the Auction Catalog, `deal_book_items` for the Deal Book - they're kept
		separate so loading one doesn't wipe out the other), compute the
		reconciliation totals, and move `status` to `status_after` once parsing
		succeeds."""
		rows = self._read_rows()
		if not rows:
			frappe.throw(_("The uploaded file has no rows."))

		header_row = rows[0]
		column_map = {}
		for idx, cell in enumerate(header_row):
			cfg = header_map.get(_normalize_header(cell))
			if cfg:
				column_map[idx] = cfg

		if not column_map:
			frappe.throw(
				_(
					"None of the expected {0} columns were found in the uploaded file. Check the file format."
				).format(source_label)
			)

		self.set(target_field, [])
		total_packages = 0
		total_net_weight = 0.0

		for raw_row in rows[1:]:
			if not any(cell is not None and str(cell).strip() not in ("", "-") for cell in raw_row):
				continue

			values = {"row_status": "Pending", "source_row_type": source_label}
			has_data = False
			for idx, cfg in column_map.items():
				cell = raw_row[idx] if idx < len(raw_row) else None
				converted = _convert_cell(cell, cfg["type"])
				values[cfg["field"]] = converted
				if converted not in (None, ""):
					has_data = True

			if not has_data:
				continue

			self.append(target_field, values)
			total_packages += cint(values.get("packages") or 0)
			total_net_weight += flt(values.get("total_net_weight") or values.get("net_weight") or 0)

		rows_list = self.get(target_field)
		self.computed_total_packages = total_packages
		self.computed_total_net_weight = total_net_weight
		self.rows_parsed = len(rows_list)
		self.rows_created = 0
		self.rows_error = 0
		self.rows_duplicate = 0
		self.rows_updated = 0
		self.status = status_after
		self.save()

		return {"rows": len(rows_list), "status": self.status, "source_type": source_label}

	def _read_rows(self) -> list:
		if not self.import_file:
			frappe.throw(_("Attach a file first."))
		file_doc = frappe.get_doc("File", {"file_url": self.import_file})
		return _read_spreadsheetml_rows(file_doc.get_full_path())

	def _get_broker_by_short_name(self, broker_code):
		"""Return the Broker name whose broker_short_name matches `broker_code`, else None."""
		if not broker_code:
			return None
		return frappe.db.get_value("Broker", {"broker_short_name": broker_code}, "name")

	@frappe.whitelist()
	def create_tea_lots(self):
		"""Create one Tea Lot per Auction Catalog row (Auction channel only, once
		the catalogue is loaded). Mirrors TeaLotImport.create_tea_lots /
		TeaLotImageImport.create_tea_lots: per-row try/except, row_status/message/
		tea_lot tracking on the child row, and a {created, errors, duplicates}
		summary. A row's own `season`/`sale_no` win when set; a blank/zero row
		value falls back to this document's own `season`/`sale_no`."""
		if self.acquisition_channel != "Auction":
			frappe.throw(_("Tea Lot creation is only available for the Auction channel."))
		if self.status != "Catalogue Loaded":
			frappe.throw(_("Load the Auction Catalog file before creating Tea Lots."))
		if not self.auction_centre:
			frappe.throw(_("Auction Centre is required."))
		if not self.items:
			frappe.throw(_("There are no rows to create Tea Lots from."))

		auction_centre_code = frappe.db.get_value(
			"Auction Centre", self.auction_centre, "auction_centre_code"
		)
		if not auction_centre_code:
			frappe.throw(_("Auction Centre Code not found."))

		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.items:
			if row.row_status == "Created":
				continue
			try:
				season = row.season or self.season
				sale_no = row.sale_no or self.sale_no

				if not season:
					row.row_status = "Error"
					row.message = _("Season is missing on this row and on the Buying Week document.")
					error += 1
					continue

				if not sale_no:
					row.row_status = "Error"
					row.message = _("Sale No is missing on this row and on the Buying Week document.")
					error += 1
					continue

				if not row.lot_no:
					row.row_status = "Error"
					row.message = _("Lot No is missing on this row.")
					error += 1
					continue

				mark_name = (row.mark_raw or "").strip()
				if not mark_name:
					row.row_status = "Error"
					row.message = _("Mark is missing on this row.")
					error += 1
					continue

				if not frappe.db.exists("Mark", mark_name):
					row.row_status = "Error"
					row.message = _("Mark '{0}' not found. Please create it first.").format(mark_name)
					error += 1
					continue

				grade_code = (row.grade_raw or "").strip()
				if grade_code and not frappe.db.exists("Grade", grade_code):
					row.row_status = "Error"
					row.message = _("Grade '{0}' not found. Please create it first.").format(grade_code)
					error += 1
					continue

				broker_code = (row.broker_code or "").strip()
				broker_name = self._get_broker_by_short_name(broker_code)
				if not broker_name:
					row.row_status = "Error"
					row.message = _("Broker code '{0}' not found in Broker (Broker Short Name).").format(
						broker_code
					)
					error += 1
					continue

				tea_lot_name = f"{auction_centre_code}-{season}-{sale_no}-{row.lot_no}"
				if frappe.db.exists("Tea Lot", tea_lot_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Lot '{0}' already exists.").format(tea_lot_name)
					duplicate += 1

					# Record this Buying Week as a reprint on the existing Tea Lot
					existing_lot = frappe.get_doc("Tea Lot", tea_lot_name)
					if not any(r.buying_week == self.name for r in existing_lot.reprints):
						existing_lot.append("reprints", {"buying_week": self.name})
						existing_lot.save(ignore_permissions=True)
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": "Auction",
					"purchase_status": self.purchase_status,
					"auction_centre": self.auction_centre,
					"mark": mark_name,
					"grade": grade_code or None,
					"lot_no": row.lot_no,
					"broker": broker_name,
					"broker_code": broker_code,
					"invoice_number": row.invoice_number,
					"packages": cint(row.packages),
					"gross_wtpkg": flt(row.gross_weight),
					"net_wtpkg": flt(row.net_weight),
					"net_weight_total": flt(row.net_weight) * cint(row.packages),
					"rate": flt(row.base_price),
					"season": season,
					"sale_no": sale_no,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
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
				frappe.log_error(frappe.get_traceback(), "Buying Week: create_tea_lots row failed")

		self.rows_created = sum(1 for item in self.items if item.row_status == "Created")
		self.rows_error = sum(1 for item in self.items if item.row_status == "Error")
		self.rows_duplicate = sum(1 for item in self.items if item.row_status == "Duplicate")
		self.save()

		return {"created": created, "errors": error, "duplicates": duplicate}

	@frappe.whitelist()
	def create_tea_purchases(self):
		"""Create one Tea Purchase per Deal Book row (Auction channel only, once
		the Deal Book is loaded). Mirrors create_tea_lots(): per-row try/except,
		row_status/message/tea_purchase tracking on the child row, and a
		{created, errors, duplicates} summary. A row's own `season`/`sale_no` win
		when set; a blank/zero row value falls back to this document's own
		`season`/`sale_no` - same rule as create_tea_lots().

		Tea Purchase uses the exact same name as the Tea Lot for the same
		physical lot (`{auction_centre_code}-{season}-{sale_no}-{lot_no}`) - if
		a Tea Lot with that name already exists (created earlier from the
		Auction Catalog), the two are linked both ways: the new Tea Purchase's
		`tea_lot` is set, and that Tea Lot's `tea_purchase` is set back to it.
		No matching Tea Lot is not an error - the purchase is recorded either
		way, just without the link."""
		if self.acquisition_channel != "Auction":
			frappe.throw(_("Tea Purchase creation is only available for the Auction channel."))
		if self.status != "Deal Book Loaded":
			frappe.throw(_("Load the Deal Book file before creating Tea Purchases."))
		if not self.auction_centre:
			frappe.throw(_("Auction Centre is required."))
		if not self.deal_book_items:
			frappe.throw(_("There are no rows to create Tea Purchases from."))

		auction_centre_code = frappe.db.get_value(
			"Auction Centre", self.auction_centre, "auction_centre_code"
		)
		if not auction_centre_code:
			frappe.throw(_("Auction Centre Code not found."))

		meta = frappe.get_meta("Tea Purchase")
		created = duplicate = error = 0

		for row in self.deal_book_items:
			if row.row_status == "Created":
				continue
			try:
				season = row.season or self.season
				sale_no = row.sale_no or self.sale_no

				if not season:
					row.row_status = "Error"
					row.message = _("Season is missing on this row and on the Buying Week document.")
					error += 1
					continue

				if not sale_no:
					row.row_status = "Error"
					row.message = _("Sale No is missing on this row and on the Buying Week document.")
					error += 1
					continue

				if not row.lot_no:
					row.row_status = "Error"
					row.message = _("Lot No is missing on this row.")
					error += 1
					continue

				mark_name = (row.mark_raw or "").strip()
				if not mark_name:
					row.row_status = "Error"
					row.message = _("Mark is missing on this row.")
					error += 1
					continue

				if not frappe.db.exists("Mark", mark_name):
					row.row_status = "Error"
					row.message = _("Mark '{0}' not found. Please create it first.").format(mark_name)
					error += 1
					continue

				grade_code = (row.grade_raw or "").strip()
				if grade_code and not frappe.db.exists("Grade", grade_code):
					row.row_status = "Error"
					row.message = _("Grade '{0}' not found. Please create it first.").format(grade_code)
					error += 1
					continue

				broker_code = (row.broker_code or "").strip()
				broker_name = self._get_broker_by_short_name(broker_code)
				if not broker_name:
					row.row_status = "Error"
					row.message = _("Broker code '{0}' not found in Broker (Broker Short Name).").format(
						broker_code
					)
					error += 1
					continue

				computed_name = f"{auction_centre_code}-{season}-{sale_no}-{row.lot_no}"
				if frappe.db.exists("Tea Purchase", computed_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Purchase '{0}' already exists.").format(computed_name)
					duplicate += 1
					continue

				matched_tea_lot = computed_name if frappe.db.exists("Tea Lot", computed_name) else None

				values = {
					"doctype": "Tea Purchase",
					"acquisition_channel": "Auction",
					"purchase_status": self.purchase_status,
					"auction_centre": self.auction_centre,
					"mark": mark_name,
					"grade": grade_code or None,
					"lot_no": row.lot_no,
					"invoice_number": row.invoice_number,
					"deal_no": row.deal_no,
					"packages": cint(row.packages),
					"net_weight_total": flt(row.total_net_weight or row.net_weight),
					"rate": flt(row.price_per_kg),
					"season": season,
					"sale_no": sale_no,
					"tea_lot": matched_tea_lot,
					"broker": broker_name,
					"broker_code": broker_code,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				purchase = frappe.get_doc(values)
				purchase.insert(ignore_permissions=True)

				if matched_tea_lot:
					frappe.db.set_value("Tea Lot", matched_tea_lot, "tea_purchase", purchase.name)

				row.tea_purchase = purchase.name
				row.tea_lot = matched_tea_lot
				row.row_status = "Created"
				row.message = _("Created {0}").format(purchase.name)
				created += 1

			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Buying Week: create_tea_purchases row failed")

		self.rows_created = sum(1 for item in self.deal_book_items if item.row_status == "Created")
		self.rows_error = sum(1 for item in self.deal_book_items if item.row_status == "Error")
		self.rows_duplicate = sum(1 for item in self.deal_book_items if item.row_status == "Duplicate")
		self.save()

		return {"created": created, "errors": error, "duplicates": duplicate}
