# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import re
import xml.etree.ElementTree as ET
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, flt, nowdate

# --------------------------------------------------------------------------- config
#
# Both weekly exports (Deal Book / Auction All Catalog) are SpreadsheetML "Excel 2003
# XML" files saved with an .xls/.xlsx-looking name - NOT real xlsx (zip) or xls
# (binary) files, so openpyxl/xlrd cannot open them. They are read with the stdlib
# xml.etree.ElementTree instead (see _read_spreadsheetml_rows). Both have a plain
# header on row 1 with no metadata block above it (unlike the Dalmia template used by
# Tea Lot Import).
#
# Only the two source files are parsed here - Tea Lot creation from Buying Day is a
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

# Private Purchase List template (real .xlsx, data in the "Example" sheet). Keyed by
# the lowercased raw header (not _normalize_header) because "Brokerage %" and
# "Brokerage" would collapse to the same key. Net kg / Value / Brokerage (amount) are
# formula columns and are recalculated by _compute_private_purchase_list instead.
PRIVATE_PURCHASE_SHEET = "Example"
HEADER_TO_FIELD_PRIVATE_PURCHASE = {
	"list no": {"field": "list_no", "type": "str"},
	"list date": {"field": "list_date", "type": "date"},
	"broker": {"field": "broker", "type": "str"},
	"seller": {"field": "seller", "type": "str"},
	"seller gstin": {"field": "seller_gstin", "type": "str"},
	"tax invoice no.": {"field": "tax_invoice_no", "type": "str"},
	"tax invoice date": {"field": "tax_invoice_date", "type": "date"},
	"warehouse": {"field": "warehouse", "type": "str"},
	"delivery": {"field": "delivery", "type": "str"},
	"transporter": {"field": "transporter", "type": "str"},
	"bilty / lr no.": {"field": "bilty_lr_no", "type": "str"},
	"lot / invoice no.": {"field": "lot_invoice_no", "type": "str"},
	"garden / mark": {"field": "mark_raw", "type": "str"},
	"grade": {"field": "grade_raw", "type": "str"},
	"packages": {"field": "packages", "type": "int"},
	"net kg per package": {"field": "net_kg_per_package", "type": "float"},
	"short packages": {"field": "short_packages", "type": "int"},
	"kg short per short package": {"field": "kg_short_per_package", "type": "float"},
	"rate per kg": {"field": "rate_per_kg", "type": "float"},
	"brokerage %": {"field": "brokerage_percent", "type": "float"},
	"bill mode": {"field": "bill_mode", "type": "str"},
	"liquor mark": {"field": "overall_rating", "type": "str"},
	"density": {"field": "density", "type": "float"},
	"for blend": {"field": "for_blend", "type": "str"},
}

# Offer Sample Evaluation sheet (first sheet; row 1 is a title, header on row 2).
# Everything is stored as text except the date.
HEADER_TO_FIELD_OFFER_SAMPLE = {
	"sl no": {"field": "sl_no", "type": "str"},
	"date": {"field": "date", "type": "date"},
	"garden": {"field": "garden", "type": "str"},
	"region": {"field": "region", "type": "str"},
	"invoice no": {"field": "invoice_no", "type": "str"},
	"grade": {"field": "grade", "type": "str"},
	"qty": {"field": "qty", "type": "str"},
	"pckgs": {"field": "pckgs", "type": "str"},
	"broker/direct from garden": {"field": "broker_direct", "type": "str"},
	"taster": {"field": "taster", "type": "str"},
	"c": {"field": "c", "type": "str"},
	"t": {"field": "t", "type": "str"},
	"s": {"field": "s", "type": "str"},
	"b": {"field": "b", "type": "str"},
	"overall rating": {"field": "overall_rating", "type": "str"},
	"remark": {"field": "remark", "type": "str"},
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
		if isinstance(value, datetime):
			return value.date()
		if hasattr(value, "year") and hasattr(value, "month"):
			return value
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


class BuyingDay(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.buying_week_deal_book_tea.buying_week_deal_book_tea import (
			BuyingWeekDealBookTea,
		)
		from lotwise.lotwise.doctype.buying_week_purchase_order.buying_week_purchase_order import (
			BuyingWeekPurchaseOrder,
		)
		from lotwise.lotwise.doctype.buying_week_tea.buying_week_tea import BuyingWeekTea
		from lotwise.lotwise.doctype.offer_sample_evaluation_item.offer_sample_evaluation_item import (
			OfferSampleEvaluationItem,
		)
		from lotwise.lotwise.doctype.private_purchase_list.private_purchase_list import PrivatePurchaseList

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		buying_week: DF.Link | None
		catalogue_file: DF.Attach | None
		company: DF.Link | None
		computed_total_net_weight: DF.Float
		computed_total_packages: DF.Int
		day: DF.Int
		deal_book_file: DF.Attach | None
		deal_book_items: DF.Table[BuyingWeekDealBookTea]
		items: DF.Table[BuyingWeekTea]
		offer_sample_evaluation: DF.Table[OfferSampleEvaluationItem]
		offer_sample_evaluation_file: DF.Attach | None
		private_purchase_list: DF.Table[PrivatePurchaseList]
		purchase_list_file: DF.Attach | None
		purchase_orders: DF.Table[BuyingWeekPurchaseOrder]
		purchase_status: DF.Link | None
		purchase_type: DF.Literal["", "Internal", "External"]
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
			"Purchase list Loaded",
			"Offer Sample Evaluation Load",
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

	def _copy_from_week(self):
		if not self.buying_week:
			frappe.throw(_("Buying Week is required."))
		week = frappe.db.get_value(
			"Buying Week",
			self.buying_week,
			["acquisition_channel", "auction_centre", "sale_no", "week_no", "season"],
			as_dict=True,
		)
		for key, value in week.items():
			self.set(key, value)

	def autoname(self):
		self._copy_from_week()
		if self.acquisition_channel == "Auction":
			if not self.auction_centre:
				frappe.throw(_("Auction Centre is required to generate the Buying Day name."))

			auction_centre_code = frappe.db.get_value(
				"Auction Centre", self.auction_centre, "auction_centre_code"
			)
			if not auction_centre_code:
				frappe.throw(_("Auction Centre Code not found."))

			if not self.season:
				frappe.throw(_("Season is required to generate the Buying Day name."))

			if not self.sale_no:
				frappe.throw(_("Sale No is required to generate the Buying Day name."))

			if not self.day:
				frappe.throw(_("Day is required to generate the Buying Day name."))

			self.name = f"BD-{auction_centre_code}-{self.season}-{self.sale_no}-{self.day}"
		elif self.acquisition_channel == "Private":
			if not self.season or not self.week_no:
				frappe.throw(_("Season and Week No are required to generate the Buying Day name."))

			# BD-{season}-{week_no}-{counter}, e.g. BD-2026-43-00008 (season-wise counter continues)
			counter = make_autoname(f"BD-{self.season}-.#####").rsplit("-", 1)[1]
			self.name = f"BD-{self.season}-{self.week_no}-{counter}"
		else:
			# Outsourced naming hasn't been specified yet - fall back to a
			# safe generic series rather than guessing.
			self.name = make_autoname("BD-.YYYY.-.#####")

	def validate(self):
		self._copy_from_week()
		self._compute_private_purchase_list()

	def _compute_private_purchase_list(self):
		for row in self.get("private_purchase_list") or []:
			row.net_kg = flt(
				flt(row.packages) * flt(row.net_kg_per_package)
				- flt(row.short_packages) * flt(row.kg_short_per_package),
				3,
			)
			row.value = flt(row.net_kg * flt(row.rate_per_kg), 2)
			row.brokerage = flt(row.value * flt(row.brokerage_percent) / 100, 2)

	def after_insert(self):
		week = frappe.get_doc("Buying Week", self.buying_week)
		if not any(r.buying_day == self.name for r in week.buying_days):
			week.append("buying_days", {"buying_day": self.name})
			week.save(ignore_permissions=True)

	def on_trash(self):
		frappe.db.delete("Buying Week Day", {"parent": self.buying_week, "buying_day": self.name})

	@frappe.whitelist()
	def export_error_rows(self, table):
		"""Export rows with row_status == 'Error' of one child table as a base64 xlsx.

		`table` is "items" (Auction Catalogue Items) or "deal_book_items" (Deal Book Items).
		"""
		import base64
		import io

		from openpyxl import Workbook

		config = {
			"items": ("Buying Week Tea", "auction_catalogue_errors"),
			"deal_book_items": ("Buying Week Deal Book Tea", "deal_book_errors"),
			"offer_sample_evaluation": ("Offer Sample Evaluation Item", "offer_sample_errors"),
		}
		if table not in config:
			frappe.throw(_("Invalid table: {0}").format(table))
		child_doctype, suffix = config[table]

		# Offer Sample rows track Tea Lot and Tea Evaluation steps separately.
		error_rows = [
			r for r in self.get(table) if r.row_status == "Error" or r.get("eval_status") == "Error"
		]
		if not error_rows:
			frappe.throw(_("No error rows to export."))

		skip = {"row_status", "message", "eval_status", "eval_message"}
		fields = [
			df
			for df in frappe.get_meta(child_doctype).fields
			if df.fieldtype not in frappe.model.no_value_fields and df.fieldname not in skip
		]

		wb = Workbook()
		ws = wb.active
		ws.title = "Errors"
		headers = ["#"] + [df.label or df.fieldname for df in fields] + ["Status", "Message"]
		for col, header in enumerate(headers, start=1):
			ws.cell(row=1, column=col, value=header)

		for row_idx, row in enumerate(error_rows, start=2):
			values = [row.idx]
			for df in fields:
				value = row.get(df.fieldname)
				values.append(
					None if value is None else (value if isinstance(value, (int, float)) else str(value))
				)
			if row.get("eval_status") == "Error" and row.row_status != "Error":
				values += [row.eval_status, row.eval_message]
			else:
				values += [row.row_status, row.message]
			for col, value in enumerate(values, start=1):
				ws.cell(row=row_idx, column=col, value=value)

		output = io.BytesIO()
		wb.save(output)
		return {
			"filename": f"{self.name}_{suffix}.xlsx",
			"content": base64.b64encode(output.getvalue()).decode("utf-8"),
		}

	@frappe.whitelist()
	def parse_auction_catalog(self):
		"""Read the attached file as an Auction All Catalog export."""
		return self._parse(
			"Auction Catalog", HEADER_TO_FIELD_AUCTION_CATALOG, "Catalogue Loaded", "items", "catalogue_file"
		)

	@frappe.whitelist()
	def parse_deal_book(self):
		"""Read the attached file as a Deal Book export."""
		return self._parse(
			"Deal Book", HEADER_TO_FIELD_DEAL_BOOK, "Deal Book Loaded", "deal_book_items", "deal_book_file"
		)

	@frappe.whitelist()
	def parse_private_purchase_list(self):
		"""Read the attached Private Purchase List xlsx ("Example" sheet) into the
		private_purchase_list child table (replaces existing rows)."""
		from openpyxl import load_workbook

		file_url = self.get("purchase_list_file")
		if not file_url:
			frappe.throw(_("Attach the {0} first.").format(self.meta.get_label("purchase_list_file")))
		path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()

		try:
			wb = load_workbook(path, data_only=True, read_only=True)
		except Exception:
			frappe.throw(_("The uploaded file is not a valid .xlsx file."))
		if PRIVATE_PURCHASE_SHEET in wb.sheetnames:
			sheet_name = PRIVATE_PURCHASE_SHEET
		elif len(wb.sheetnames) == 1:
			sheet_name = wb.sheetnames[0]
		else:
			frappe.throw(
				_("Sheet '{0}' was not found in the uploaded file. Sheets found: {1}").format(
					PRIVATE_PURCHASE_SHEET, ", ".join(wb.sheetnames)
				)
			)

		rows = list(wb[sheet_name].iter_rows(values_only=True))
		if not rows:
			frappe.throw(_("The uploaded file has no rows."))

		column_map = {}
		for idx, cell in enumerate(rows[0]):
			cfg = HEADER_TO_FIELD_PRIVATE_PURCHASE.get(str(cell or "").strip().lower())
			if cfg:
				column_map[idx] = cfg
		if not column_map:
			frappe.throw(
				_("None of the expected Private Purchase List columns were found. Check the file format.")
			)

		self.set("private_purchase_list", [])
		for raw_row in rows[1:]:
			# The table is one contiguous block; the first fully blank row ends it
			# (anything below, e.g. the explanatory note, is not data).
			if not any(c is not None and str(c).strip() != "" for c in raw_row):
				break
			values = {"row_status": "Pending"}
			for idx, cfg in column_map.items():
				cell = raw_row[idx] if idx < len(raw_row) else None
				values[cfg["field"]] = _convert_cell(cell, cfg["type"])
			if not any(v not in (None, "") for k, v in values.items() if k != "row_status"):
				continue
			# The template has no Delivery column; the field is mandatory.
			values["delivery"] = values.get("delivery") or "Garden delivers"
			self.append("private_purchase_list", values)

		count = len(self.private_purchase_list)
		self.save()
		return {"rows": count, "status": self.status, "source_type": "Private Purchase List"}

	@frappe.whitelist()
	def parse_offer_sample_evaluation(self):
		"""Read the attached Offer Sample Evaluation xlsx into the
		offer_sample_evaluation child table (replaces existing rows)."""
		from openpyxl import load_workbook

		file_url = self.get("offer_sample_evaluation_file")
		if not file_url:
			frappe.throw(
				_("Attach the {0} first.").format(self.meta.get_label("offer_sample_evaluation_file"))
			)
		if any(r.tea_lot for r in self.offer_sample_evaluation):
			frappe.throw(_("Tea Lots are already created from these rows. Re-parsing is not allowed."))
		path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()

		try:
			wb = load_workbook(path, data_only=True, read_only=True)
		except Exception:
			frappe.throw(_("The uploaded file is not a valid .xlsx file."))
		rows = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))

		# The header is the first row with at least 3 known column names (a title
		# row may sit above it).
		header_idx, column_map = None, {}
		for r_idx, row in enumerate(rows):
			found = {
				i: HEADER_TO_FIELD_OFFER_SAMPLE[str(c).strip().lower()]
				for i, c in enumerate(row)
				if c is not None and str(c).strip().lower() in HEADER_TO_FIELD_OFFER_SAMPLE
			}
			if len(found) >= 3:
				header_idx, column_map = r_idx, found
				break
		if header_idx is None:
			frappe.throw(
				_("None of the expected Offer Sample Evaluation columns were found. Check the file format.")
			)

		self.set("offer_sample_evaluation", [])
		for raw_row in rows[header_idx + 1 :]:
			if not any(c is not None and str(c).strip() != "" for c in raw_row):
				break
			values = {}
			for idx, cfg in column_map.items():
				cell = raw_row[idx] if idx < len(raw_row) else None
				values[cfg["field"]] = _convert_cell(cell, cfg["type"])
			self.append("offer_sample_evaluation", values)

		count = len(self.offer_sample_evaluation)
		self.save()
		return {"rows": count, "status": self.status, "source_type": "Offer Sample Evaluation"}

	def _parse(
		self,
		source_label: str,
		header_map: dict,
		status_after: str,
		target_field: str = "items",
		file_field: str = "catalogue_file",
	) -> dict:
		"""Shared body for parse_auction_catalog/parse_deal_book: read the attached
		file with `header_map`, replace the `target_field` child table (`items` for
		the Auction Catalog, `deal_book_items` for the Deal Book - they're kept
		separate so loading one doesn't wipe out the other), compute the
		reconciliation totals, and move `status` to `status_after` once parsing
		succeeds."""
		rows = self._read_rows(file_field)
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

	def _read_rows(self, file_field: str) -> list:
		file_url = self.get(file_field)
		if not file_url:
			frappe.throw(_("Attach the {0} first.").format(self.meta.get_label(file_field)))
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		return _read_spreadsheetml_rows(file_doc.get_full_path())

	def _get_broker_by_short_name(self, broker_code):
		"""Return the Auction Broker name whose broker_short_name matches `broker_code` and
		whose Auction Centre is this document's Auction Centre, else None."""
		if not broker_code:
			return None
		return frappe.db.get_value(
			"Broker",
			{
				"broker_short_name": broker_code,
				"auction_centre": self.auction_centre,
				"acquisition_channel": "Auction",
			},
			"name",
		)

	@frappe.whitelist()
	def create_tea_lots_from_offer_samples(self):
		"""Create one Private Tea Lot per Offer Sample Evaluation row. Garden maps to
		Mark; qty is the net weight per package. Per-row try/except with
		row_status/message/tea_lot tracking and a {created, errors, duplicates} summary."""
		if self.acquisition_channel != "Private":
			frappe.throw(_("Tea Lot creation from Offer Samples is only available for the Private channel."))
		if self.status != "Offer Sample Evaluation Load":
			frappe.throw(_("Load the Offer Sample Evaluation file before creating Tea Lots."))
		if not self.offer_sample_evaluation:
			frappe.throw(_("There are no rows to create Tea Lots from."))
		if not self.season:
			frappe.throw(_("Season is required on the Buying Day."))
		if not self.week_no:
			frappe.throw(_("Week No is required on the Buying Day."))

		from lotwise.lotwise.doctype.tea_lot.tea_lot import get_private_tea_lot_name

		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.offer_sample_evaluation:
			if row.row_status == "Created":
				continue
			try:
				mark_name = (row.garden or "").strip()
				if not mark_name:
					row.row_status = "Error"
					row.message = _("Garden (Mark) is missing on this row.")
					error += 1
					continue
				if not frappe.db.exists("Mark", mark_name):
					row.row_status = "Error"
					row.message = _("Mark '{0}' not found. Please create it first.").format(mark_name)
					error += 1
					continue

				invoice = (row.invoice_no or "").strip()
				if not invoice:
					row.row_status = "Error"
					row.message = _("Invoice No is missing on this row.")
					error += 1
					continue

				grade_code = (row.grade or "").strip()
				if not grade_code:
					row.row_status = "Error"
					row.message = _("Grade is missing on this row.")
					error += 1
					continue
				if not frappe.db.exists("Grade", grade_code):
					row.row_status = "Error"
					row.message = _("Grade '{0}' not found. Please create it first.").format(grade_code)
					error += 1
					continue

				try:
					net_wt = flt((row.qty or "0").replace(",", ""))
					packages = cint(flt((row.pckgs or "0").replace(",", "")))
				except ValueError:
					row.row_status = "Error"
					row.message = _("Qty / Pckgs must be numbers.")
					error += 1
					continue

				broker_text = (row.broker_direct or "").strip()
				broker = None
				if broker_text and broker_text.upper() != "DIRECT":
					broker = frappe.db.get_value(
						"Broker",
						{"broker_name": broker_text, "acquisition_channel": "Private"},
						"name",
					)
					if not broker:
						row.row_status = "Error"
						row.message = _("Private Broker '{0}' not found.").format(broker_text)
						error += 1
						continue

				tea_lot_name = get_private_tea_lot_name(
					mark_name, invoice, grade_code, self.season, self.week_no
				)
				if frappe.db.exists("Tea Lot", tea_lot_name):
					row.row_status = "Duplicate"
					row.tea_lot = tea_lot_name
					row.message = _("Tea Lot '{0}' already exists.").format(tea_lot_name)
					duplicate += 1
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": "Private",
					"purchase_status": "Offer",
					"mark": mark_name,
					"grade": grade_code,
					"invoice_number": invoice,
					"season": self.season,
					"week_no": self.week_no,
					"packages": packages,
					"net_wtpkg": net_wt,
					"net_weight_total": net_wt * packages,
					"offer_date": row.date,
					"broker": broker,
					"purchase_type": self.purchase_type,
					"region": (row.region or "").strip() or None,
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
				frappe.clear_last_message()
				frappe.log_error(
					frappe.get_traceback(), "Buying Day: create_tea_lots_from_offer_samples row failed"
				)

		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}

	@frappe.whitelist()
	def create_tea_evaluations_from_offer_samples(self):
		"""Create one Tea Evaluation (stage "Offer Sample", dated today) per Offer Sample
		Evaluation row that already has a Tea Lot. Taster, Evaluation Stage and Quality
		Grade must exist in their masters; otherwise the row is marked Error."""
		if self.acquisition_channel != "Private":
			frappe.throw(_("Tea Evaluation from Offer Samples is only available for the Private channel."))
		if self.status != "Offer Sample Evaluation Load":
			frappe.throw(_("Load the Offer Sample Evaluation file before creating Tea Evaluations."))
		if not any(r.tea_lot for r in self.offer_sample_evaluation):
			frappe.throw(_("Create Tea Lots first. No row has a Tea Lot yet."))

		stage = "Offer Sample"
		evaluation_date = nowdate()
		created = duplicate = error = 0

		def set_error(row, message):
			row.eval_status = "Error"
			row.eval_message = message

		for row in self.offer_sample_evaluation:
			if row.eval_status == "Created":
				continue
			try:
				if not row.tea_lot:
					set_error(row, _("Create the Tea Lot for this row first."))
					error += 1
					continue

				taster = (row.taster or "").strip()
				if not taster:
					set_error(row, _("Taster is missing on this row."))
					error += 1
					continue
				if not frappe.db.exists("Taster", taster):
					set_error(row, _("Taster '{0}' not found in Taster master.").format(taster))
					error += 1
					continue

				if not frappe.db.exists("Evaluation Stage", stage):
					set_error(
						row, _("Evaluation Stage '{0}' not found. Please create it first.").format(stage)
					)
					error += 1
					continue

				quality_grade = (row.overall_rating or "").strip()
				if quality_grade and not frappe.db.exists("Quality Grade", quality_grade):
					set_error(
						row, _("Quality Grade '{0}' not found. Please create it first.").format(quality_grade)
					)
					error += 1
					continue

				scores = {}
				for label, source, target in (
					("C", row.c, "colour"),
					("T", row.t, "taste"),
					("S", row.s, "strength"),
					("B", row.b, "briskness"),
				):
					try:
						scores[target] = cint(flt((source or "0").replace(",", "")))
					except ValueError:
						raise_msg = _("{0} must be a number.").format(label)
						set_error(row, raise_msg)
						scores = None
						break
				if scores is None:
					error += 1
					continue

				existing = frappe.db.get_value(
					"Tea Evaluation",
					{
						"tea_lot": row.tea_lot,
						"taster": taster,
						"evaluation_stage": stage,
						"evaluation_date": evaluation_date,
					},
					"name",
				)
				if existing:
					row.evaluation = existing
					row.eval_status = "Duplicate"
					row.eval_message = _("Tea Evaluation '{0}' already exists.").format(existing)
					duplicate += 1
					continue

				# Tea Evaluation.on_update copies its valuations onto the Tea Lot, so carry the
				# lot's current values over to avoid blanking them.
				lot_valuation = (
					frappe.db.get_value(
						"Tea Lot", row.tea_lot, ["suggested_valuation", "actual_valuation"], as_dict=True
					)
					or {}
				)

				evaluation = frappe.get_doc(
					{
						"doctype": "Tea Evaluation",
						"tea_lot": row.tea_lot,
						"taster": taster,
						"evaluation_date": evaluation_date,
						"evaluation_stage": stage,
						"quality_grade": quality_grade or None,
						"invoice_number": (row.invoice_no or "").strip() or None,
						"mark": (row.garden or "").strip() or None,
						"remarks": (row.remark or "").strip() or None,
						"suggested_valuation": lot_valuation.get("suggested_valuation"),
						"actual_valuation": lot_valuation.get("actual_valuation"),
						**scores,
					}
				)
				evaluation.insert(ignore_permissions=True)

				row.evaluation = evaluation.name
				row.eval_status = "Created"
				row.eval_message = _("Created {0}").format(evaluation.name)
				created += 1

			except Exception as e:
				set_error(row, str(e)[:140])
				error += 1
				frappe.clear_last_message()
				frappe.log_error(
					frappe.get_traceback(), "Buying Day: create_tea_evaluations_from_offer_samples row failed"
				)

		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}

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
					row.message = _("Season is missing on this row and on the Buying Day document.")
					error += 1
					continue

				if not sale_no:
					row.row_status = "Error"
					row.message = _("Sale No is missing on this row and on the Buying Day document.")
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
					row.message = _("Broker code '{0}' not found for Auction Centre '{1}'.").format(
						broker_code, self.auction_centre
					)
					error += 1
					continue

				warehouse_raw = (row.warehouse_name or "").strip()
				if not warehouse_raw:
					row.row_status = "Error"
					row.message = _("Warehouse Name is missing on this row.")
					error += 1
					continue

				warehouse = frappe.db.exists("Warehouse", warehouse_raw) or frappe.db.get_value(
					"Warehouse", {"warehouse_name": warehouse_raw}, "name"
				)
				if not warehouse:
					row.row_status = "Error"
					row.message = _("Warehouse '{0}' not found. Please create it first.").format(
						warehouse_raw
					)
					error += 1
					continue

				tea_lot_name = f"{auction_centre_code}-{season}-{sale_no}-{row.lot_no}"
				if frappe.db.exists("Tea Lot", tea_lot_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Lot '{0}' already exists.").format(tea_lot_name)
					duplicate += 1

					# Record this Buying Day as a reprint on the existing Tea Lot
					existing_lot = frappe.get_doc("Tea Lot", tea_lot_name)
					if not any(r.buying_day == self.name for r in existing_lot.reprints):
						existing_lot.append("reprints", {"buying_day": self.name})
						existing_lot.save(ignore_permissions=True)
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": "Auction",
					"purchase_status": self.purchase_status,
					"auction_centre": self.auction_centre,
					"mark": mark_name,
					"grade": grade_code or None,
					"category": (row.category_id or "").strip() or None,
					"lot_no": row.lot_no,
					"broker": broker_name,
					"broker_code": broker_code,
					"warehouse": warehouse,
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
				frappe.log_error(frappe.get_traceback(), "Buying Day: create_tea_lots row failed")

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
		physical lot (`{auction_centre_code}-{season}-{sale_no}-{lot_no}`). The
		Tea Lot (created earlier from the Auction Catalog) must already exist:
		the two are linked both ways - the new Tea Purchase's `tea_lot` is set,
		and that Tea Lot's `tea_purchase` is set back to it. If no matching Tea
		Lot exists, the row is marked Error and no Tea Purchase is created."""
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
					row.message = _("Season is missing on this row and on the Buying Day document.")
					error += 1
					continue

				if not sale_no:
					row.row_status = "Error"
					row.message = _("Sale No is missing on this row and on the Buying Day document.")
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
					row.message = _("Broker code '{0}' not found for Auction Centre '{1}'.").format(
						broker_code, self.auction_centre
					)
					error += 1
					continue

				computed_name = f"{auction_centre_code}-{season}-{sale_no}-{row.lot_no}"
				if frappe.db.exists("Tea Purchase", computed_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Purchase '{0}' already exists.").format(computed_name)
					duplicate += 1
					continue

				if not frappe.db.exists("Tea Lot", computed_name):
					row.row_status = "Error"
					row.message = _(
						"Tea Lot '{0}' does not exist. Please create the Tea Lot before creating the Tea Purchase."
					).format(computed_name)
					error += 1
					continue

				matched_tea_lot = computed_name
				warehouse, category = frappe.db.get_value(
					"Tea Lot", matched_tea_lot, ["warehouse", "category"]
				)

				values = {
					"doctype": "Tea Purchase",
					"acquisition_channel": "Auction",
					"purchase_status": self.purchase_status,
					"auction_centre": self.auction_centre,
					"mark": mark_name,
					"grade": grade_code or None,
					"category": category,
					"lot_no": row.lot_no,
					"invoice_number": row.invoice_number,
					"deal_no": row.deal_no,
					"packages": cint(row.packages),
					"net_weight_total": flt(row.total_net_weight or row.net_weight),
					"rate": flt(row.price_per_kg),
					"season": season,
					"sale_no": sale_no,
					"tea_lot": matched_tea_lot,
					"warehouse": warehouse,
					"broker": broker_name,
					"broker_code": broker_code,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				purchase = frappe.get_doc(values)
				purchase.insert(ignore_permissions=True)

				tea_lot_updates = {"tea_purchase": purchase.name}
				if self.purchase_status:
					tea_lot_updates["purchase_status"] = self.purchase_status
				frappe.db.set_value("Tea Lot", matched_tea_lot, tea_lot_updates)

				row.tea_purchase = purchase.name
				row.tea_lot = matched_tea_lot
				row.warehouse = purchase.warehouse
				row.category = purchase.category
				row.broker = purchase.broker
				row.item_code = purchase.item
				row.batch_no = purchase.batch_no
				row.row_status = "Created"
				row.message = _("Created {0}").format(purchase.name)
				created += 1

			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Buying Day: create_tea_purchases row failed")

		self.rows_created = sum(1 for item in self.deal_book_items if item.row_status == "Created")
		self.rows_error = sum(1 for item in self.deal_book_items if item.row_status == "Error")
		self.rows_duplicate = sum(1 for item in self.deal_book_items if item.row_status == "Duplicate")
		self.save()

		return {"created": created, "errors": error, "duplicates": duplicate}

	def _resolve_warehouse(self, raw):
		"""Sheet holds the warehouse_name; the record name carries a company suffix."""
		raw = (raw or "").strip()
		filters = {"warehouse_name": raw}
		if self.company:
			filters["company"] = self.company
		return frappe.db.get_value("Warehouse", filters, "name") or frappe.db.exists("Warehouse", raw)

	@frappe.whitelist()
	def create_tea_lots_from_private_purchase_list(self):
		"""External purchases only: create one Private Tea Lot per Private Purchase
		List row and store its id in the row's `tea_lot`, so Tea Purchases can then be
		created from it. Returns {created, errors, duplicates}."""
		if self.acquisition_channel != "Private" or self.purchase_type != "External":
			frappe.throw(_("This is only available for Private External purchases."))
		if self.status != "Purchase list Loaded":
			frappe.throw(_("Load the Private Purchase List file before creating Tea Lots."))
		if not self.private_purchase_list:
			frappe.throw(_("There are no rows to create Tea Lots from."))
		if not self.season:
			frappe.throw(_("Season is required on the Buying Day."))
		if not self.week_no:
			frappe.throw(_("Week No is required on the Buying Day."))

		from lotwise.lotwise.doctype.tea_lot.tea_lot import get_private_tea_lot_name

		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.private_purchase_list:
			if row.tea_lot:
				continue
			try:
				mark_name = (row.mark_raw or "").strip()
				invoice = (row.lot_invoice_no or "").strip()
				grade_code = (row.grade_raw or "").strip()

				if not mark_name:
					row.row_status = "Error"
					row.message = _("Garden / Mark is missing on this row.")
					error += 1
					continue
				if not frappe.db.exists("Mark", mark_name):
					row.row_status = "Error"
					row.message = _("Mark '{0}' not found. Please create it first.").format(mark_name)
					error += 1
					continue
				if not invoice:
					row.row_status = "Error"
					row.message = _("Lot / Invoice No is missing on this row.")
					error += 1
					continue
				if not grade_code:
					row.row_status = "Error"
					row.message = _("Grade is missing on this row.")
					error += 1
					continue
				if not frappe.db.exists("Grade", grade_code):
					row.row_status = "Error"
					row.message = _("Grade '{0}' not found. Please create it first.").format(grade_code)
					error += 1
					continue

				warehouse = None
				warehouse_raw = (row.warehouse or "").strip()
				if warehouse_raw:
					warehouse = self._resolve_warehouse(warehouse_raw)
					if not warehouse:
						row.row_status = "Error"
						row.message = _("Warehouse '{0}' not found for company '{1}'.").format(
							warehouse_raw, self.company or ""
						)
						error += 1
						continue

				tea_lot_name = get_private_tea_lot_name(
					mark_name, invoice, grade_code, self.season, self.week_no
				)
				if frappe.db.exists("Tea Lot", tea_lot_name):
					row.row_status = "Duplicate"
					row.tea_lot = tea_lot_name
					row.message = _("Tea Lot '{0}' already exists.").format(tea_lot_name)
					duplicate += 1
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": "Private",
					"purchase_status": self.purchase_status,
					"purchase_type": self.purchase_type,
					"mark": mark_name,
					"grade": grade_code,
					"category": "CTC",
					"invoice_number": invoice,
					"season": self.season,
					"week_no": self.week_no,
					"packages": cint(row.packages),
					"net_wtpkg": flt(row.net_kg_per_package),
					"net_weight_total": flt(row.net_kg),
					"rate": flt(row.rate_per_kg),
					"warehouse": warehouse,
					"broker": row.broker,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				lot = frappe.get_doc(values)
				lot.insert(ignore_permissions=True)

				row.tea_lot = lot.name
				row.row_status = "Created"
				row.message = _("Created Tea Lot {0}").format(lot.name)
				created += 1

			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.clear_last_message()
				frappe.log_error(
					frappe.get_traceback(),
					"Buying Day: create_tea_lots_from_private_purchase_list row failed",
				)

		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}

	@frappe.whitelist()
	def create_private_tea_purchases(self):
		"""Create one Tea Purchase per Private Purchase List row (Private channel,
		once the purchase list is loaded). Same rules as create_tea_purchases():
		the Tea Lot with the same name (PVT-{season}-{week_no}-{grade}-{mark}-{invoice})
		must already exist, otherwise the row is marked Error and nothing is
		created. For External purchases the Tea Lot id comes from the row's
		`tea_lot` (set by create_tea_lots_from_private_purchase_list). Returns {created, errors, duplicates}."""
		if self.acquisition_channel != "Private":
			frappe.throw(_("This Tea Purchase creation is only available for the Private channel."))
		if self.status != "Purchase list Loaded":
			frappe.throw(_("Load the Private Purchase List file before creating Tea Purchases."))
		if not self.private_purchase_list:
			frappe.throw(_("There are no rows to create Tea Purchases from."))
		if not self.season:
			frappe.throw(_("Season is required on the Buying Day."))
		if not self.week_no:
			frappe.throw(_("Week No is required on the Buying Day."))

		from lotwise.lotwise.doctype.tea_lot.tea_lot import get_private_tea_lot_name

		meta = frappe.get_meta("Tea Purchase")
		external = self.purchase_type == "External"
		created = duplicate = error = 0

		for row in self.private_purchase_list:
			if row.tea_purchase:
				# Backfill Item / Batch on rows created before those columns existed
				if not (row.item_code and row.batch_no):
					item, batch_no = frappe.db.get_value(
						"Tea Purchase", row.tea_purchase, ["item", "batch_no"]
					) or (None, None)
					row.item_code = row.item_code or item
					row.batch_no = row.batch_no or batch_no
				continue
			try:
				mark_name = (row.mark_raw or "").strip()
				invoice = (row.lot_invoice_no or "").strip()
				grade_code = (row.grade_raw or "").strip()

				if not mark_name:
					row.row_status = "Error"
					row.message = _("Garden / Mark is missing on this row.")
					error += 1
					continue
				if not invoice:
					row.row_status = "Error"
					row.message = _("Lot / Invoice No is missing on this row.")
					error += 1
					continue
				if not grade_code:
					row.row_status = "Error"
					row.message = _("Grade is missing on this row.")
					error += 1
					continue

				if external:
					computed_name = row.tea_lot
					if not computed_name or not frappe.db.exists("Tea Lot", computed_name):
						row.row_status = "Error"
						row.message = _("Create the Tea Lot for this row first.")
						error += 1
						continue
				else:
					computed_name = get_private_tea_lot_name(
						mark_name, invoice, grade_code, self.season, self.week_no
					)
				if frappe.db.exists("Tea Purchase", computed_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Purchase '{0}' already exists.").format(computed_name)
					duplicate += 1
					continue

				if not frappe.db.exists("Tea Lot", computed_name):
					row.row_status = "Error"
					row.message = _(
						"Tea Lot '{0}' does not exist. Please create the Tea Lot before creating the Tea Purchase."
					).format(computed_name)
					error += 1
					continue

				lot_warehouse = frappe.db.get_value("Tea Lot", computed_name, "warehouse")

				warehouse_raw = (row.warehouse or "").strip()
				if warehouse_raw:
					warehouse = self._resolve_warehouse(warehouse_raw)
					if not warehouse:
						row.row_status = "Error"
						row.message = _("Warehouse '{0}' not found for company '{1}'.").format(
							warehouse_raw, self.company or ""
						)
						error += 1
						continue
				else:
					warehouse = lot_warehouse

				values = {
					"doctype": "Tea Purchase",
					"acquisition_channel": "Private",
					"purchase_status": self.purchase_status,
					"mark": mark_name,
					"grade": grade_code,
					"category": "CTC",
					"invoice_number": invoice,
					"packages": cint(row.packages),
					"net_weight_total": flt(row.net_kg),
					"rate": flt(row.rate_per_kg),
					"season": self.season,
					"week_no": self.week_no,
					"tea_lot": computed_name,
					"warehouse": warehouse,
					"broker": row.broker,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				purchase = frappe.get_doc(values)
				purchase.insert(ignore_permissions=True)

				tea_lot_updates = {"tea_purchase": purchase.name}
				if self.purchase_status:
					tea_lot_updates["purchase_status"] = self.purchase_status
				frappe.db.set_value("Tea Lot", computed_name, tea_lot_updates)

				row.tea_purchase = purchase.name
				row.tea_lot = computed_name
				row.item_code = purchase.item
				row.batch_no = purchase.batch_no
				row.row_status = "Created"
				row.message = _("Created {0}").format(purchase.name)
				created += 1

			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(
					frappe.get_traceback(), "Buying Day: create_private_tea_purchases row failed"
				)

		self.save()

		return {"created": created, "errors": error, "duplicates": duplicate}

	@frappe.whitelist()
	def create_purchase_orders(self):
		"""Create one draft Purchase Order per Broker from the Deal Book rows that
		already have a Batch (created with their Tea Purchase). The supplier is the
		Broker's `supplier`; the PO date is the date part of the row's Deal Time
		(dd/mm/yyyy hh:mm:ss). Rows already carrying a `purchase_order` are skipped,
		so the button is safe to press again. Each PO is recorded in the
		`purchase_orders` table; when every batch row has a PO the status becomes
		"Ordered"."""
		if self.acquisition_channel != "Auction":
			frappe.throw(_("Purchase Order creation is only available for the Auction channel."))
		if not self.deal_book_items:
			frappe.throw(_("There are no Deal Book rows to create Purchase Orders from."))
		if not self.company:
			frappe.throw(_("Company is required to create Purchase Orders."))

		groups = {}
		for row in self.deal_book_items:
			if not row.batch_no or row.purchase_order:
				continue
			if not row.broker:
				row.message = _("Broker is missing on this row.")
				continue
			groups.setdefault(row.broker, []).append(row)

		created = error = 0

		for broker, rows in groups.items():
			try:
				supplier = frappe.db.get_value("Broker", broker, "supplier")
				if not supplier:
					raise frappe.ValidationError(_("Broker '{0}' has no Supplier.").format(broker))

				deal_date = self._deal_date(rows[0].deal_time)

				po = frappe.get_doc(
					{
						"doctype": "Purchase Order",
						"supplier": supplier,
						"company": self.company,
						"transaction_date": deal_date,
						"schedule_date": deal_date,
						"items": [
							{
								"item_code": r.item_code,
								"batch_no": r.batch_no,
								"qty": flt(r.total_net_weight or r.net_weight),
								"rate": flt(r.price_per_kg),
								"warehouse": r.warehouse,
								"schedule_date": deal_date,
							}
							for r in rows
						],
					}
				)
				po.insert(ignore_permissions=True)

				for r in rows:
					r.purchase_order = po.name
					r.message = _("PO {0}").format(po.name)
				self.append(
					"purchase_orders",
					{
						"broker": broker,
						"supplier": supplier,
						"purchase_order": po.name,
						"deal_date": deal_date,
					},
				)
				created += 1

			except Exception as e:
				for r in rows:
					r.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Buying Day: create_purchase_orders failed")

		if (
			self.deal_book_items
			and all(r.purchase_order for r in self.deal_book_items if r.batch_no)
			and any(r.batch_no for r in self.deal_book_items)
		):
			self.status = "Ordered"
		self.save()

		return {"created": created, "errors": error}

	@frappe.whitelist()
	def create_private_purchase_orders(self):
		"""Create draft Purchase Orders from Private Purchase List rows that already
		have a Batch. One PO per Seller + Tax Invoice No; when there is no invoice
		number yet, one PO per Seller + Bill Mode. Rows already carrying a
		`purchase_order` are skipped. The supplier is matched on the seller name and
		the PO date is the row's List Date. Returns {created, errors}."""
		if self.acquisition_channel != "Private":
			frappe.throw(_("This Purchase Order creation is only available for the Private channel."))
		if not self.private_purchase_list:
			frappe.throw(_("There are no Private Purchase List rows to create Purchase Orders from."))
		if not self.company:
			frappe.throw(_("Company is required to create Purchase Orders."))

		groups = {}
		for row in self.private_purchase_list:
			if not row.batch_no or row.purchase_order:
				continue
			seller = (row.seller or "").strip()
			if not seller:
				row.message = _("Seller is missing on this row.")
				continue
			invoice = (row.tax_invoice_no or "").strip()
			key = (seller, invoice) if invoice else (seller, (row.bill_mode or "").strip())
			groups.setdefault(key, []).append(row)

		created = error = 0

		for (seller, _ref), rows in groups.items():
			try:
				supplier = frappe.db.get_value(
					"Supplier", {"supplier_name": seller}, "name"
				) or frappe.db.exists("Supplier", seller)
				if not supplier:
					raise frappe.ValidationError(_("Supplier '{0}' not found.").format(seller))

				list_date = rows[0].list_date or nowdate()

				items = []
				for r in rows:
					warehouse = None
					if (r.warehouse or "").strip():
						warehouse = self._resolve_warehouse(r.warehouse)
						if not warehouse:
							raise frappe.ValidationError(
								_("Warehouse '{0}' not found for company '{1}'.").format(
									r.warehouse, self.company
								)
							)
					elif r.tea_lot:
						warehouse = frappe.db.get_value("Tea Lot", r.tea_lot, "warehouse")
					items.append(
						{
							"item_code": r.item_code,
							"batch_no": r.batch_no,
							"qty": flt(r.net_kg),
							"rate": flt(r.rate_per_kg),
							"warehouse": warehouse,
							"schedule_date": list_date,
						}
					)

				po = frappe.get_doc(
					{
						"doctype": "Purchase Order",
						"supplier": supplier,
						"company": self.company,
						"transaction_date": list_date,
						"schedule_date": list_date,
						"items": items,
					}
				)
				po.insert(ignore_permissions=True)

				for r in rows:
					r.purchase_order = po.name
					r.message = _("PO {0}").format(po.name)
				self.append(
					"purchase_orders",
					{"supplier": supplier, "purchase_order": po.name, "deal_date": list_date},
				)
				created += 1

			except Exception as e:
				for r in rows:
					r.message = str(e)[:140]
				error += 1
				frappe.clear_last_message()
				frappe.log_error(frappe.get_traceback(), "Buying Day: create_private_purchase_orders failed")

		batch_rows = [r for r in self.private_purchase_list if r.batch_no]
		if batch_rows and all(r.purchase_order for r in batch_rows):
			self.status = "Ordered"
		self.save()

		return {"created": created, "errors": error}

	@staticmethod
	def _deal_date(deal_time):
		"""Date part of a Deal Time such as '25/09/2026 11:30:00'."""
		date_part = (deal_time or "").strip().split(" ")[0]
		try:
			return datetime.strptime(date_part, "%d/%m/%Y").date()
		except ValueError:
			raise frappe.ValidationError(_("Deal Time '{0}' is not in dd/mm/yyyy format.").format(deal_time))
