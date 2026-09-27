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
