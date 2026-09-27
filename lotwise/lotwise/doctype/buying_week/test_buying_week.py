# Copyright (c) 2026, BusinessThat.Works and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from lotwise.lotwise.doctype.buying_week import buying_week as mod

_XML_HEADER = (
	'<?xml version="1.0" encoding="utf-8"?>\n'
	'<?mso-application progid="Excel.Sheet"?>\n'
	'<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n'
	'  <ss:Worksheet ss:Name="Sheet1">\n'
	"    <ss:Table>\n"
)
_XML_FOOTER = "    </ss:Table>\n  </ss:Worksheet>\n</ss:Workbook>\n"


def _row_xml(cells):
	"""Build one <ss:Row> with the given cell values. A float is written as a
	Number cell, everything else as a String cell - matching what the real
	exports do."""
	out = ["      <ss:Row>\n"]
	for value in cells:
		if isinstance(value, (int, float)) and not isinstance(value, bool):
			out.append(f'        <ss:Cell><ss:Data ss:Type="Number">{value}</ss:Data></ss:Cell>\n')
		else:
			out.append(f'        <ss:Cell><ss:Data ss:Type="String">{value}</ss:Data></ss:Cell>\n')
	out.append("      </ss:Row>\n")
	return "".join(out)


def _make_spreadsheetml(rows):
	return _XML_HEADER + "".join(_row_xml(r) for r in rows) + _XML_FOOTER


class TestBuyingWeekHelpers(FrappeTestCase):
	"""Pure-function tests - no DB/file access needed."""

	def test_normalize_header(self):
		self.assertEqual(mod._normalize_header("LotNo"), "lotno")
		self.assertEqual(mod._normalize_header("LOT NO"), "lot no")
		self.assertEqual(mod._normalize_header("Qty (Pkgs)"), "qty pkgs")
		self.assertEqual(mod._normalize_header(None), "")

	def test_convert_cell_blank_and_dash_are_none(self):
		self.assertIsNone(mod._convert_cell("", "str"))
		self.assertIsNone(mod._convert_cell("-", "str"))
		self.assertIsNone(mod._convert_cell(None, "float"))

	def test_convert_cell_types(self):
		self.assertEqual(mod._convert_cell("30", "int"), 30)
		self.assertEqual(mod._convert_cell(30.0, "int"), 30)
		self.assertEqual(mod._convert_cell("40.47", "float"), 40.47)
		self.assertEqual(mod._convert_cell(" GHATIAROYAL ", "str"), "GHATIAROYAL")
		self.assertEqual(mod._convert_cell("01/09/2026", "date"), frappe.utils.getdate("2026-09-01"))
		self.assertIsNone(mod._convert_cell("not-a-date", "date"))

	def test_read_spreadsheetml_rows(self):
		xml = _make_spreadsheetml(
			[
				["LotNo", "Mark", "Qty (Pkgs)"],
				["JT0059", "BINAGURI", 25],
			]
		)
		path = frappe.utils.get_files_path("test_buying_week_sample.xml", is_private=1)
		with open(path, "w", encoding="utf-8") as f:
			f.write(xml)
		try:
			rows = mod._read_spreadsheetml_rows(path)
			self.assertEqual(rows[0], ["LotNo", "Mark", "Qty (Pkgs)"])
			self.assertEqual(rows[1], ["JT0059", "BINAGURI", 25.0])
		finally:
			import os

			os.remove(path)


class TestBuyingWeekParseFile(FrappeTestCase):
	"""End-to-end: attach a small SpreadsheetML file and run parse_auction_catalog()/parse_deal_book()."""

	def setUp(self):
		if not frappe.db.exists("Purchase Status", "Test Purchased"):
			frappe.get_doc({"doctype": "Purchase Status", "purchase_status": "Test Purchased"}).insert(
				ignore_permissions=True
			)

	def _attach(self, doc, xml_content, filename):
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"content": xml_content,
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"is_private": 1,
			}
		)
		file_doc.insert(ignore_permissions=True)
		doc.import_file = file_doc.file_url
		doc.save(ignore_permissions=True)

	def test_parse_deal_book(self):
		doc = frappe.get_doc(
			{
				"doctype": "Buying Week",
				"acquisition_channel": "Outsourced",
				"purchase_status": "Test Purchased",
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		xml = _make_spreadsheetml(
			[
				[
					"LotNo",
					"Mark",
					"Grade",
					"Qty (Pkgs)",
					"Invoice No",
					"Price/Kg",
					"Auct. Val",
					"BasePrice",
					"Total GrossWt",
					"NtWt",
					"Total NtWt",
					"Type",
					"DealNo",
				],
				[
					"JT0059",
					"BINAGURI",
					"OF",
					25,
					"C955",
					304,
					355,
					1,
					955.5,
					950,
					941.4,
					"Leaf",
					"27703301",
				],
			]
		)
		self._attach(doc, xml, "deal_book_test.xls")

		result = doc.parse_deal_book()

		self.assertEqual(result["rows"], 1)
		self.assertEqual(doc.rows_parsed, 1)
		row = doc.items[0]
		self.assertEqual(row.lot_no, "JT0059")
		self.assertEqual(row.mark_raw, "BINAGURI")
		self.assertEqual(row.packages, 25)
		self.assertEqual(row.deal_no, "27703301")
		self.assertEqual(row.source_row_type, "Deal Book")
		self.assertEqual(row.row_status, "Pending")
		self.assertEqual(doc.computed_total_packages, 25)
		self.assertEqual(doc.computed_total_net_weight, 941.4)
		self.assertEqual(doc.status, "Deal Book Loaded")

	def test_parse_auction_catalog(self):
		doc = frappe.get_doc(
			{
				"doctype": "Buying Week",
				"acquisition_channel": "Outsourced",
				"purchase_status": "Test Purchased",
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		xml = _make_spreadsheetml(
			[
				[
					"Season",
					"Sale No",
					"LOT NO",
					"Auctioneer",
					"MarkCode",
					"GradeCode",
					"NoOfPacks",
					"GrossWeight",
					"NetWeight",
					"Lot Type",
					"InvoiceNo",
					"Warehouse Name",
				],
				[
					2026,
					36,
					"JT0001",
					"JT",
					"GHATIAROYAL",
					"BP",
					30,
					40.47,
					40.00,
					"Sold",
					"UK1019",
					"KTTWPL - UNIT - 1",
				],
			]
		)
		self._attach(doc, xml, "auction_catalog_test.xls")

		result = doc.parse_auction_catalog()

		self.assertEqual(result["rows"], 1)
		row = doc.items[0]
		self.assertEqual(row.lot_no, "JT0001")
		self.assertEqual(row.mark_raw, "GHATIAROYAL")
		self.assertEqual(row.packages, 30)
		self.assertEqual(row.lot_type, "Sold")
		self.assertEqual(row.warehouse_name, "KTTWPL - UNIT - 1")
		self.assertEqual(row.source_row_type, "Auction Catalog")
		self.assertEqual(doc.computed_total_packages, 30)
		# No total_net_weight column in this format - falls back to net_weight
		self.assertEqual(doc.computed_total_net_weight, 40.00)
		self.assertEqual(doc.status, "Catalogue Loaded")


class TestBuyingWeekCreateTeaLots(FrappeTestCase):
	"""create_tea_lots(): Auction Catalog rows -> Tea Lot."""

	def setUp(self):
		if not frappe.db.exists("Auction Centre", "Test Siliguri BW"):
			frappe.get_doc(
				{
					"doctype": "Auction Centre",
					"auction_centre": "Test Siliguri BW",
					"auction_centre_code": "TSLGBW",
				}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Purchase Status", "Test Purchased BW"):
			frappe.get_doc({"doctype": "Purchase Status", "purchase_status": "Test Purchased BW"}).insert(
				ignore_permissions=True
			)
		if not frappe.db.exists("Mark", "TESTMARK BW"):
			frappe.get_doc({"doctype": "Mark", "mark_name": "TESTMARK BW"}).insert(ignore_permissions=True)

	def _make_doc(self, items, sale_no=777):
		doc = frappe.get_doc(
			{
				"doctype": "Buying Week",
				"acquisition_channel": "Auction",
				"auction_centre": "Test Siliguri BW",
				"sale_no": sale_no,
				"season": 2025,
				"status": "Catalogue Loaded",
				"purchase_status": "Test Purchased BW",
				"items": items,
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		return doc

	def test_create_tea_lot_computes_weight_and_name(self):
		doc = self._make_doc(
			sale_no=778,
			items=[
				{
					"lot_no": "BWCT001",
					"mark_raw": "TESTMARK BW",
					"packages": 30,
					"gross_weight": 40.47,
					"net_weight": 40.0,
					"base_price": 1,
					"season": 2026,
					"sale_no": 36,
					"row_status": "Pending",
					"source_row_type": "Auction Catalog",
				}
			],
		)

		result = doc.create_tea_lots()

		self.assertEqual(result, {"created": 1, "errors": 0, "duplicates": 0})
		row = doc.items[0]
		self.assertEqual(row.row_status, "Created")
		# Row's own season/sale_no (2026/36) win over the doc's (2025/777)
		self.assertEqual(row.tea_lot, "TSLGBW-2026-36-BWCT001")

		lot = frappe.db.get_value(
			"Tea Lot",
			row.tea_lot,
			["gross_wtpkg", "net_wtpkg", "net_weight_total", "packages", "rate", "purchase_status"],
			as_dict=True,
		)
		self.assertEqual(lot.gross_wtpkg, 40.47)
		self.assertEqual(lot.net_wtpkg, 40.0)
		self.assertEqual(lot.net_weight_total, 40.0 * 30)  # computed: per-pkg net x packages
		self.assertEqual(lot.purchase_status, "Test Purchased BW")

		# Re-running is idempotent - the already-created row is skipped
		result2 = doc.create_tea_lots()
		self.assertEqual(result2, {"created": 0, "errors": 0, "duplicates": 0})

	def test_create_tea_lot_falls_back_to_doc_season_and_sale_no(self):
		doc = self._make_doc(
			sale_no=779,
			items=[
				{
					"lot_no": "BWCT002",
					"mark_raw": "TESTMARK BW",
					"packages": 10,
					"gross_weight": 40,
					"net_weight": 38,
					"base_price": 200,
					"season": 0,
					"sale_no": 0,
					"row_status": "Pending",
					"source_row_type": "Auction Catalog",
				}
			],
		)

		doc.create_tea_lots()

		row = doc.items[0]
		self.assertEqual(row.row_status, "Created")
		# Row's season/sale_no are blank - falls back to the doc's own 2025/779
		self.assertEqual(row.tea_lot, "TSLGBW-2025-779-BWCT002")

	def test_create_tea_lot_errors_on_unknown_mark(self):
		doc = self._make_doc(
			sale_no=780,
			items=[
				{
					"lot_no": "BWCT003",
					"mark_raw": "NO SUCH MARK BW",
					"packages": 10,
					"gross_weight": 40,
					"net_weight": 38,
					"base_price": 200,
					"season": 2026,
					"sale_no": 40,
					"row_status": "Pending",
					"source_row_type": "Auction Catalog",
				}
			],
		)

		result = doc.create_tea_lots()

		self.assertEqual(result, {"created": 0, "errors": 1, "duplicates": 0})
		self.assertEqual(doc.items[0].row_status, "Error")
		self.assertIn("not found", doc.items[0].message)


class TestBuyingWeekCreateTeaPurchases(FrappeTestCase):
	"""create_tea_purchases(): Deal Book rows -> Tea Purchase, linked back to a
	Tea Lot created earlier from the same (single, reused) Buying Week doc."""

	def setUp(self):
		if not frappe.db.exists("Auction Centre", "Test Siliguri TPU"):
			frappe.get_doc(
				{
					"doctype": "Auction Centre",
					"auction_centre": "Test Siliguri TPU",
					"auction_centre_code": "TSLGTPU",
				}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Purchase Status", "Test Purchased TPU"):
			frappe.get_doc({"doctype": "Purchase Status", "purchase_status": "Test Purchased TPU"}).insert(
				ignore_permissions=True
			)
		if not frappe.db.exists("Mark", "TESTMARK TPU"):
			frappe.get_doc({"doctype": "Mark", "mark_name": "TESTMARK TPU"}).insert(ignore_permissions=True)

	def test_create_tea_purchase_links_to_existing_tea_lot_and_falls_back(self):
		# Naming (auction_centre + season + sale_no) means this is ONE document
		# reused across the pipeline - catalogue loaded and lots created first,
		# then the same doc switches to Deal Book Loaded for the purchase step.
		doc = frappe.get_doc(
			{
				"doctype": "Buying Week",
				"acquisition_channel": "Auction",
				"auction_centre": "Test Siliguri TPU",
				"sale_no": 950,
				"season": 2025,
				"status": "Catalogue Loaded",
				"purchase_status": "Test Purchased TPU",
				"items": [
					{
						"lot_no": "TPU001",
						"mark_raw": "TESTMARK TPU",
						"packages": 20,
						"gross_weight": 40,
						"net_weight": 39,
						"base_price": 250,
						"season": 2025,
						"sale_no": 950,
						"row_status": "Pending",
						"source_row_type": "Auction Catalog",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		doc.create_tea_lots()
		lot_name = doc.items[0].tea_lot
		self.assertEqual(lot_name, "TSLGTPU-2025-950-TPU001")

		doc.status = "Deal Book Loaded"
		doc.set(
			"items",
			[
				{
					# matches the Tea Lot above
					"lot_no": "TPU001",
					"mark_raw": "TESTMARK TPU",
					"packages": 20,
					"total_net_weight": 780,
					"price_per_kg": 260,
					"deal_no": "DEAL001",
					"season": 2025,
					"sale_no": 950,
					"row_status": "Pending",
					"source_row_type": "Deal Book",
				},
				{
					# no matching Tea Lot, and blank row season/sale_no -> falls back to doc's
					"lot_no": "TPU002",
					"mark_raw": "TESTMARK TPU",
					"packages": 5,
					"total_net_weight": 190,
					"price_per_kg": 200,
					"deal_no": "DEAL002",
					"season": 0,
					"sale_no": 0,
					"row_status": "Pending",
					"source_row_type": "Deal Book",
				},
			],
		)
		doc.save(ignore_permissions=True)

		result = doc.create_tea_purchases()

		self.assertEqual(result, {"created": 2, "errors": 0, "duplicates": 0})
		row1, row2 = doc.items[0], doc.items[1]
		self.assertEqual(row1.tea_purchase, lot_name)  # same computed name as the Tea Lot
		self.assertEqual(row2.tea_purchase, "TSLGTPU-2025-950-TPU002")

		purchase1 = frappe.db.get_value(
			"Tea Purchase", row1.tea_purchase, ["tea_lot", "rate", "net_weight_total"], as_dict=True
		)
		self.assertEqual(purchase1.tea_lot, lot_name)
		self.assertEqual(purchase1.rate, 260)
		self.assertEqual(purchase1.net_weight_total, 780)

		purchase2_tea_lot = frappe.db.get_value("Tea Purchase", row2.tea_purchase, "tea_lot")
		self.assertFalse(purchase2_tea_lot)

		# Bidirectional: the Tea Lot's own tea_purchase field points back
		self.assertEqual(frappe.db.get_value("Tea Lot", lot_name, "tea_purchase"), row1.tea_purchase)
