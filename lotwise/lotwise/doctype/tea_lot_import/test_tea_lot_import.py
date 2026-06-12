# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestTeaLotImport(IntegrationTestCase):
# 	"""
# 	Integration tests for TeaLotImport.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
import openpyxl
from frappe.tests.utils import FrappeTestCase

from lotwise.lotwise.doctype.tea_lot_import.tea_lot_import import (
	_find_header,
	_label_value,
	_norm,
	_read_rows,
)


def _build_sample_sheet(shuffle=False):
	"""Build a workbook resembling the agent purchase list.

	When shuffle=True the data columns are reordered and the header block is
	pushed down, to prove the parser is position-independent.
	"""
	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = "DALMIA"

	# header metadata block
	ws["B2"] = "AUCTION PURCHASE DETAILS"
	ws["B3"] = "COMPANY :"
	ws["B5"] = "DALMIA TEA PACKAGING PVT LTD."
	ws["F7"] = "Date :"
	ws["G7"] = "2026-04-01"
	ws["C7"] = "Blend Type :"
	ws["D7"] = "PREMIUM PACK"
	ws["M3"] = "AUCTION"
	ws["M4"] = "SILIGURI"
	ws["N3"] = "SALE NO."
	ws["N4"] = 2

	# column order
	if shuffle:
		cols = [
			"Grade",
			"Lot No.",
			"Garden / Mark",
			"Invoice No.",
			"Density",
			"No of Pkgs.",
			"Wt (Kgs.)",
			"Nett. Wt. Kg",
			"Rate / Kg.",
			"Liquor Mark",
		]
		header_row = 12
	else:
		cols = [
			"Lot No.",
			"Invoice No.",
			"Garden / Mark",
			"Grade",
			"No of  Pkgs.",
			"Wt (Kgs.)",
			"Nett. Wt.  Kg",
			"Rate / Kg.",
			"Density",
			"Liquor Mark",
		]
		header_row = 8

	for i, label in enumerate(cols, start=2):
		ws.cell(header_row, i, label)

	# five data rows keyed by column label
	data = [
		{
			"Lot No.": "SC4502",
			"Invoice No.": "DC123",
			"Mark": "MALBAZAR",
			"Grade": "BP",
			"Pkgs": 15,
			"Wt": 35,
			"Net": 519.2,
			"Rate": 380,
			"Density": 2.9,
			"Liquor": "C+",
		},
		{
			"Lot No.": "TY1234",
			"Invoice No.": "PJ145",
			"Mark": "CHALSA",
			"Grade": "BP",
			"Pkgs": 15,
			"Wt": 35,
			"Net": 519.2,
			"Rate": 210,
			"Density": 2.9,
			"Liquor": "C+",
		},
		{
			"Lot No.": "GH0023",
			"Invoice No.": "D12",
			"Mark": "MATELLI",
			"Grade": "OF",
			"Pkgs": 15,
			"Wt": 35,
			"Net": 519.2,
			"Rate": 250,
			"Density": 3.05,
			"Liquor": "C+",
		},
		{
			"Lot No.": "RT7895",
			"Invoice No.": "DS142",
			"Mark": "BANARHAT",
			"Grade": "BP",
			"Pkgs": 20,
			"Wt": 38,
			"Net": 751.4,
			"Rate": 360,
			"Density": 2.7,
			"Liquor": "B",
		},
		{
			"Lot No.": "CTY489",
			"Invoice No.": "CDL",
			"Mark": "BARODIGHI",
			"Grade": "BP",
			"Pkgs": 22,
			"Wt": 38,
			"Net": 827.4,
			"Rate": 275,
			"Density": 2.7,
			"Liquor": "B",
		},
	]

	def put(r, label, value):
		for i, lab in enumerate(cols, start=2):
			if lab.strip().startswith(label):
				ws.cell(r, i, value)
				return

	r = header_row + 2  # leave a gap row, like the real sheet
	for d in data:
		put(r, "Lot No", d["Lot No."])
		put(r, "Invoice", d["Invoice No."])
		put(r, "Garden", d["Mark"])
		put(r, "Grade", d["Grade"])
		put(r, "No of", d["Pkgs"])
		put(r, "Wt (", d["Wt"])
		put(r, "Nett", d["Net"])
		put(r, "Rate", d["Rate"])
		put(r, "Density", d["Density"])
		put(r, "Liquor", d["Liquor"])
		r += 1

	# page total row
	ws.cell(r + 1, 2, "PAGE  TOTAL :")
	put(r + 1, "No of", 87)
	put(r + 1, "Nett", 3136.4)
	return wb


class TestTeaLotImportParser(FrappeTestCase):
	def test_norm(self):
		self.assertEqual(_norm("Nett. Wt.  Kg"), "nett wt kg")
		self.assertEqual(_norm("Rate / Kg."), "rate kg")
		self.assertEqual(_norm(None), "")

	def test_header_and_rows_default_layout(self):
		ws = _build_sample_sheet(shuffle=False).active
		hr, colmap = _find_header(ws)
		self.assertIsNotNone(hr)
		for f in (
			"lot_no",
			"invoice_number",
			"mark_raw",
			"grade_raw",
			"packages",
			"net_weight_total",
			"rate",
			"density",
			"liquor_mark",
		):
			self.assertIn(f, colmap)
		rows, totals = _read_rows(ws, hr, colmap)
		self.assertEqual(len(rows), 5)
		self.assertEqual(rows[0]["lot_no"], "SC4502")
		self.assertEqual(rows[0]["liquor_mark"], "C+")
		self.assertEqual(sum(r["packages"] for r in rows), 87)
		self.assertAlmostEqual(sum(r["net_weight_total"] for r in rows), 3136.4, places=1)
		self.assertEqual(totals["packages"], 87)
		self.assertAlmostEqual(totals["net_weight_total"], 3136.4, places=1)

	def test_header_survives_reordered_columns(self):
		ws = _build_sample_sheet(shuffle=True).active
		hr, colmap = _find_header(ws)
		self.assertIsNotNone(hr)
		rows, _t = _read_rows(ws, hr, colmap)
		self.assertEqual(len(rows), 5)
		# mapping still correct despite reordering
		self.assertEqual(rows[2]["mark_raw"], "MATELLI")
		self.assertEqual(rows[2]["grade_raw"], "OF")

	def test_metadata_labels(self):
		ws = _build_sample_sheet(shuffle=False).active
		self.assertEqual(str(_label_value(ws, ["sale no"])), "2")
		self.assertEqual(_label_value(ws, ["auction", "centre"]), "SILIGURI")
		self.assertEqual(_label_value(ws, ["blend type", "blend"]), "PREMIUM PACK")


class TestTeaLotImportCreate(FrappeTestCase):
	"""End-to-end create + dedup. Requires the Tea Lot doctype and masters to exist.

	Builds the import items directly (bypassing the file attach) so the test does
	not depend on File plumbing.
	"""

	# def setUp(self):
	# 	# Packing "PS" must exist because Tea Lot.packing is a Link defaulting to PS.
	# 	if not frappe.db.exists("Packing", "PS"):
	# 		frappe.get_doc({"doctype": "Packing", "packing_code": "PS",
	# 						"description": "Paper Sack"}).insert(ignore_permissions=True)
	def setUp(self):
		"""Clean stale test data before each test."""
		# Delete test Tea Lots
		for lot in frappe.get_all("Tea Lot", filters={"lot_no": ["in", ["SC4502", "ZZ1", "ZZ2"]]}):
			try:
				frappe.delete_doc("Tea Lot", lot.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		# Delete test Marks
		for mark in frappe.get_all("Mark", filters={"mark_name": ["in", ["MALBAZAR", "TESTGARDEN"]]}):
			try:
				frappe.delete_doc("Mark", mark.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		# Delete test Estates
		for estate in frappe.get_all("Estate", filters={"estate_name": ["in", ["MALBAZAR", "TESTGARDEN"]]}):
			try:
				frappe.delete_doc("Estate", estate.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		# Delete test Grades
		for grade in frappe.get_all("Grade", filters={"grade_code": ["in", ["BP", "OF"]]}):
			try:
				frappe.delete_doc("Grade", grade.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		# Ensure Packing "PS" exists
		if not frappe.db.exists("Packing", "PS"):
			frappe.get_doc({"doctype": "Packing", "packing_code": "PS", "description": "Paper Sack"}).insert(
				ignore_permissions=True
			)

	def _make_import(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "2",
				"centre": "SILIGURI",
				"blend": "PREMIUM PACK",
				"purchase_date": "2026-04-01",
				"items": [
					{
						"lot_no": "SC4502",
						"invoice_number": "DC123",
						"mark_raw": "MALBAZAR",
						"grade_raw": "BP",
						"packages": 15,
						"gross_wtpkg": 35,
						"net_weight_total": 519.2,
						"rate": 380,
						"density": 2.9,
						"liquor_mark": "C+",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		return doc

	def test_create_and_dedup(self):
		doc = self._make_import()
		res = doc.create_tea_lots()
		self.assertEqual(res["created"], 1)

		lot_name = doc.items[0].tea_lot
		self.assertTrue(lot_name)
		lot = frappe.get_doc("Tea Lot", lot_name)
		self.assertEqual(lot.mark, "MALBAZAR")
		self.assertEqual(lot.liquor_mark, "C+")
		self.assertEqual(lot.acquisition_channel, "Auction")
		self.assertTrue(frappe.db.exists("Mark", "MALBAZAR"))
		self.assertTrue(frappe.db.exists("Estate", "MALBAZAR"))
		self.assertTrue(frappe.db.exists("Grade", "BP"))

		# re-import the same sheet → duplicate, no new lot
		doc2 = self._make_import()
		res2 = doc2.create_tea_lots()
		self.assertEqual(res2["created"], 0)
		self.assertEqual(res2["duplicates"], 1)

	def test_invalid_liquor_and_missing_mandatory(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "2",
				"purchase_date": "2026-04-01",
				"items": [
					{
						"lot_no": "ZZ1",
						"invoice_number": "INV1",
						"mark_raw": "TESTGARDEN",
						"grade_raw": "BP",
						"liquor_mark": "Z",
						"row_status": "Pending",
					},
					{
						"lot_no": "ZZ2",
						"invoice_number": "",
						"mark_raw": "TESTGARDEN",
						"grade_raw": "BP",
						"row_status": "Pending",
					},
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		res = doc.create_tea_lots()
		self.assertEqual(res["created"], 0)
		self.assertEqual(res["errors"], 2)
