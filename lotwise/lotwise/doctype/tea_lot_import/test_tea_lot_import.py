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


import frappe
from frappe.tests.utils import FrappeTestCase


class TestTeaLotImportCreate(FrappeTestCase):
	"""Test creating Tea Lots from parsed items"""

	def setUp(self):
		"""Clean up test data"""
		for lot in frappe.get_all("Tea Lot", filters={"lot_no": ["in", ["TEST001", "TEST002", "TEST003"]]}):
			try:
				frappe.delete_doc("Tea Lot", lot.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		if not frappe.db.exists("Packing", "PS"):
			frappe.get_doc({"doctype": "Packing", "packing_code": "PS", "description": "Paper Sack"}).insert(
				ignore_permissions=True
			)

		if not frappe.db.exists("Purchase Status", "Test Purchased"):
			frappe.get_doc({"doctype": "Purchase Status", "purchase_status": "Test Purchased"}).insert(
				ignore_permissions=True
			)

		if not frappe.db.exists("Mark", "TESTMARK"):
			frappe.get_doc({"doctype": "Mark", "mark_name": "TESTMARK"}).insert(ignore_permissions=True)

		if not frappe.db.exists("Grade", "BP"):
			frappe.get_doc({"doctype": "Grade", "grade_code": "BP"}).insert(ignore_permissions=True)

		if not frappe.db.exists("Liquor Mark", "C+"):
			frappe.get_doc({"doctype": "Liquor Mark", "liquor_mark": "C+"}).insert(ignore_permissions=True)

		if not frappe.db.exists("Fiscal Year", "2026-2027"):
			frappe.get_doc(
				{
					"doctype": "Fiscal Year",
					"year": "2026-2027",
					"year_start_date": "2026-04-01",
					"year_end_date": "2027-03-31",
				}
			).insert(ignore_permissions=True)

	def test_create_tea_lots(self):
		"""Test create_tea_lots creates records correctly"""
		# Create import with 1 item
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "2",
				"centre": "SILIGURI",
				"purchase_date": "2026-04-01",
				"purchase_status": "Test Purchased",
				"items": [
					{
						"lot_no": "TEST001",
						"invoice_number": "INV001",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"purchase_date": "2026-04-01",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		# Create lots
		result = doc.create_tea_lots()

		# Verify
		self.assertEqual(result["created"], 1)
		self.assertEqual(result["errors"], 0)
		lot_name = doc.items[0].tea_lot
		self.assertTrue(frappe.db.exists("Tea Lot", lot_name))

		# Verify purchase_status is copied dynamically from the import doc, not hardcoded
		self.assertEqual(frappe.db.get_value("Tea Lot", lot_name, "purchase_status"), "Test Purchased")

	def test_create_tea_lots_offer_status_requires_offer_date(self):
		"""Offer rows without an Offer Date should error cleanly, not crash."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "3",
				"purchase_status": "Offer",
				"items": [
					{
						"lot_no": "TEST002",
						"invoice_number": "INV002",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		result = doc.create_tea_lots()

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["errors"], 1)
		self.assertIn("Offer Date", doc.items[0].message)

	def test_create_tea_lots_offer_status_with_offer_date(self):
		"""Offer rows with an Offer Date should create the Tea Lot using it for naming."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "4",
				"purchase_status": "Offer",
				"items": [
					{
						"lot_no": "TEST002",
						"invoice_number": "INV002",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"offer_date": "2026-05-01",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		result = doc.create_tea_lots()

		self.assertEqual(result["created"], 1)
		self.assertEqual(result["errors"], 0)
		lot_name = doc.items[0].tea_lot
		lot = frappe.db.get_value("Tea Lot", lot_name, ["purchase_status", "offer_date"], as_dict=True)
		self.assertEqual(lot.purchase_status, "Offer")
		self.assertEqual(str(lot.offer_date), "2026-05-01")

	def test_create_tea_lots_rejects_date_outside_fiscal_year(self):
		"""Rows whose purchase_date falls outside the selected Fiscal Year should error, not create a lot."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "5",
				"purchase_status": "Test Purchased",
				"fiscal_year": "2026-2027",
				"items": [
					{
						"lot_no": "TEST003",
						"invoice_number": "INV003",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"purchase_date": "2025-12-31",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		result = doc.create_tea_lots()

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["errors"], 1)
		self.assertIn("must fall within Fiscal Year", doc.items[0].message)
		self.assertFalse(frappe.db.exists("Tea Lot", "SLG-TESTMARK-TEST003-5-25"))

	def test_create_tea_lots_accepts_date_inside_fiscal_year(self):
		"""Rows whose purchase_date falls inside the selected Fiscal Year should create the lot normally."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "6",
				"purchase_status": "Test Purchased",
				"fiscal_year": "2026-2027",
				"items": [
					{
						"lot_no": "TEST003",
						"invoice_number": "INV003",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"purchase_date": "2026-06-01",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		result = doc.create_tea_lots()

		self.assertEqual(result["created"], 1)
		self.assertEqual(result["errors"], 0)
		lot_name = doc.items[0].tea_lot
		self.assertEqual(frappe.db.get_value("Tea Lot", lot_name, "fiscal_year"), "2026-2027")
