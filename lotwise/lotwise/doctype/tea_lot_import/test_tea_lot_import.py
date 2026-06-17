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
		for lot in frappe.get_all("Tea Lot", filters={"lot_no": ["in", ["TEST001", "TEST002"]]}):
			try:
				frappe.delete_doc("Tea Lot", lot.name, ignore_permissions=True, force=True)
			except Exception:
				pass

		if not frappe.db.exists("Packing", "PS"):
			frappe.get_doc({"doctype": "Packing", "packing_code": "PS", "description": "Paper Sack"}).insert(
				ignore_permissions=True
			)

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
				"items": [
					{
						"lot_no": "TEST001",
						"invoice_number": "INV001",
						"mark_raw": "TESTMARK",
						"grade_raw": "BP",
						"packages": 15,
						"net_weight_total": 519.2,
						"liquor_mark": "C+",
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
