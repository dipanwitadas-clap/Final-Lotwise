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
		for lot in frappe.get_all(
			"Tea Lot",
			filters={
				"lot_no": [
					"in",
					["TEST001", "TEST002", "TEST003", "TEST004", "TEST005", "TEST006", "TEST007"],
				]
			},
		):
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

		for status in ["Offer", "Purchase", "Bag Sample"]:
			if not frappe.db.exists("Purchase Status", status):
				frappe.get_doc({"doctype": "Purchase Status", "purchase_status": status}).insert(
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
				"season": "2026",
				"centre": "SILIGURI",
				"purchase_date": "2026-04-01",
				"purchase_status": "Test Purchased",
				"fiscal_year": "2026-2027",
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
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
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
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
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

	def test_create_tea_lots_accepts_date_inside_fiscal_year(self):
		"""Rows whose purchase_date falls inside the selected Fiscal Year should create the lot normally."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "6",
				"season": "2026",
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

	def test_purchase_import_updates_existing_offer_lot_in_place(self):
		"""A Purchase-phase row matching an existing Offer lot (by centre+mark+lot_no+sale_no+
		fiscal_year) should update that same Tea Lot instead of creating a duplicate."""
		offer_doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "7",
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
				"items": [
					{
						"lot_no": "TEST004",
						"invoice_number": "INV004",
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
		offer_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		offer_result = offer_doc.create_tea_lots()
		self.assertEqual(offer_result["created"], 1)
		offer_lot_name = offer_doc.items[0].tea_lot

		purchase_doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "7",
				"season": "2026",
				"purchase_status": "Test Purchased",
				"fiscal_year": "2026-2027",
				"items": [
					{
						"lot_no": "TEST004",
						"invoice_number": "INV004",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"purchase_date": "2026-07-15",
						"purchase_invoice_no": "PINV-004",
						"rate": 250,
						"row_status": "Pending",
					}
				],
			}
		)
		purchase_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		purchase_result = purchase_doc.create_tea_lots()

		self.assertEqual(purchase_result["created"], 0)
		self.assertEqual(purchase_result["updated"], 1)
		self.assertEqual(purchase_result["duplicates"], 0)
		self.assertEqual(purchase_doc.items[0].row_status, "Updated")
		self.assertEqual(purchase_doc.items[0].tea_lot, offer_lot_name)

		self.assertEqual(frappe.db.count("Tea Lot", filters={"lot_no": "TEST004"}), 1)

		lot = frappe.db.get_value(
			"Tea Lot",
			offer_lot_name,
			["purchase_status", "purchase_date", "purchase_invoice_no", "offer_date"],
			as_dict=True,
		)
		self.assertEqual(lot.purchase_status, "Test Purchased")
		self.assertEqual(str(lot.purchase_date), "2026-07-15")
		self.assertEqual(lot.purchase_invoice_no, "PINV-004")
		self.assertEqual(str(lot.offer_date), "2026-05-01")

	def test_offer_import_re_upload_is_plain_duplicate(self):
		"""Re-uploading the same Offer row (matching an existing Offer lot) should just be
		marked Duplicate and skipped, not update the existing lot."""
		item = {
			"lot_no": "TEST005",
			"invoice_number": "INV005",
			"mark_raw": "TESTMARK",
			"grade_raw": "BP",
			"packages": 15,
			"net_weight_total": 519.2,
			"liquor_mark": "C+",
			"auction_centre": "Siliguri",
			"offer_date": "2026-05-01",
			"row_status": "Pending",
		}

		doc1 = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "8",
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
				"items": [dict(item)],
			}
		)
		doc1.insert(ignore_permissions=True, ignore_mandatory=True)
		self.assertEqual(doc1.create_tea_lots()["created"], 1)

		doc2 = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "8",
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
				"items": [dict(item)],
			}
		)
		doc2.insert(ignore_permissions=True, ignore_mandatory=True)
		result2 = doc2.create_tea_lots()

		self.assertEqual(result2["created"], 0)
		self.assertEqual(result2["updated"], 0)
		self.assertEqual(result2["duplicates"], 1)
		self.assertEqual(doc2.items[0].row_status, "Duplicate")
		self.assertEqual(frappe.db.count("Tea Lot", filters={"lot_no": "TEST005"}), 1)

	def test_offer_purchase_bag_sample_lifecycle(self):
		"""offer_check/purchase_check should track the lot's lifecycle across imports,
		and a Bag Sample import should only advance purchase_status, not overwrite
		the purchase data set during the Purchase stage."""
		base_item = {
			"lot_no": "TEST006",
			"invoice_number": "INV006",
			"mark_raw": "TESTMARK",
			"grade_raw": "BP",
			"packages": 15,
			"net_weight_total": 519.2,
			"liquor_mark": "C+",
			"auction_centre": "Siliguri",
			"row_status": "Pending",
		}

		offer_doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "9",
				"season": "2026",
				"purchase_status": "Offer",
				"fiscal_year": "2026-2027",
				"items": [dict(base_item, offer_date="2026-05-01")],
			}
		)
		offer_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.assertEqual(offer_doc.create_tea_lots()["created"], 1)
		lot_name = offer_doc.items[0].tea_lot

		lot = frappe.db.get_value(
			"Tea Lot", lot_name, ["purchase_status", "offer_check", "purchase_check"], as_dict=True
		)
		self.assertEqual(lot.purchase_status, "Offer")
		self.assertEqual(lot.offer_check, 1)
		self.assertEqual(lot.purchase_check, 0)

		purchase_doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "9",
				"season": "2026",
				"purchase_status": "Purchase",
				"fiscal_year": "2026-2027",
				"items": [
					dict(
						base_item,
						purchase_date="2026-07-15",
						purchase_invoice_no="PINV-006",
						rate=250,
					)
				],
			}
		)
		purchase_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		purchase_result = purchase_doc.create_tea_lots()
		self.assertEqual(purchase_result["updated"], 1)
		self.assertEqual(purchase_doc.items[0].tea_lot, lot_name)

		lot = frappe.db.get_value(
			"Tea Lot",
			lot_name,
			["purchase_status", "offer_check", "purchase_check", "purchase_date", "purchase_invoice_no"],
			as_dict=True,
		)
		self.assertEqual(lot.purchase_status, "Purchase")
		self.assertEqual(lot.offer_check, 1)
		self.assertEqual(lot.purchase_check, 1)
		self.assertEqual(str(lot.purchase_date), "2026-07-15")
		self.assertEqual(lot.purchase_invoice_no, "PINV-006")

		bag_sample_doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "9",
				"season": "2026",
				"purchase_status": "Bag Sample",
				"fiscal_year": "2026-2027",
				"items": [dict(base_item)],
			}
		)
		bag_sample_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		bag_sample_result = bag_sample_doc.create_tea_lots()
		self.assertEqual(bag_sample_result["updated"], 1)
		self.assertEqual(bag_sample_doc.items[0].tea_lot, lot_name)

		lot = frappe.db.get_value(
			"Tea Lot",
			lot_name,
			["purchase_status", "offer_check", "purchase_check", "purchase_date", "purchase_invoice_no"],
			as_dict=True,
		)
		self.assertEqual(lot.purchase_status, "Bag Sample")
		self.assertEqual(lot.offer_check, 1)
		self.assertEqual(lot.purchase_check, 1)
		# Purchase-stage data must be preserved, not overwritten by the Bag Sample import
		self.assertEqual(str(lot.purchase_date), "2026-07-15")
		self.assertEqual(lot.purchase_invoice_no, "PINV-006")

		self.assertEqual(frappe.db.count("Tea Lot", filters={"lot_no": "TEST006"}), 1)

	def test_bag_sample_without_matching_lot_errors(self):
		"""A Bag Sample row with no prior Offer/Purchase Tea Lot should error, not create one."""
		doc = frappe.get_doc(
			{
				"doctype": "Tea Lot Import",
				"acquisition_channel": "Auction",
				"sale_no": "10",
				"season": "2026",
				"purchase_status": "Bag Sample",
				"fiscal_year": "2026-2027",
				"items": [
					{
						"lot_no": "TEST007",
						"invoice_number": "INV007",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
						"auction_centre": "Siliguri",
						"purchase_date": "2026-07-15",
						"row_status": "Pending",
					}
				],
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		result = doc.create_tea_lots()

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["updated"], 0)
		self.assertEqual(result["errors"], 1)
		self.assertEqual(doc.items[0].row_status, "Error")
		self.assertIn("No existing Tea Lot found", doc.items[0].message)
		self.assertFalse(frappe.db.exists("Tea Lot", {"lot_no": "TEST007"}))
