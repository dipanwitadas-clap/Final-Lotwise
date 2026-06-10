# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestTeaLot(IntegrationTestCase):
# 	"""
# 	Integration tests for TeaLot.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestTeaLot(FrappeTestCase):
	def setUp(self):
		"""Create test dependencies."""
		self.seller = frappe.get_doc({"doctype": "Seller", "seller_name": "Test Seller Lot"}).insert()

		self.estate = frappe.get_doc({"doctype": "Estate", "estate_name": "Test Estate Lot"}).insert()

		self.mark = frappe.get_doc(
			{"doctype": "Mark", "mark_name": "Test Mark Lot", "estate": self.estate.name}
		).insert()

		self.grade = frappe.get_doc(
			{"doctype": "Grade", "grade_code": "BOP_LOT", "description": "Test"}
		).insert()

		# Create test packing
		self.packing = frappe.get_doc(
			{"doctype": "Packing", "packing_code": "TEST_PS", "description": "Test Paper Sack"}
		).insert()

	def test_create_private_lot(self):
		"""Should create private lot with common core."""
		lot = frappe.get_doc(
			{
				"doctype": "Tea Lot",
				"acquisition_channel": "Private",
				"seller": self.seller.name,
				"mark": self.mark.name,
				"grade": self.grade.name,
				"invoice_number": "INV-001",
				"packing": self.packing.name,
				"packages": 20,
				"net_weight_total": 595.70,
			}
		).insert()

		self.assertEqual(lot.acquisition_channel, "Private")
		self.assertEqual(lot.status, "Offered")
		frappe.delete_doc("Tea Lot", lot.name)

	def test_mandatory_fields_enforced(self):
		"""Should require common core fields."""
		lot = frappe.get_doc({"doctype": "Tea Lot", "acquisition_channel": "Private"})
		self.assertRaises(frappe.ValidationError, lot.insert)

	def tearDown(self):
		"""Cleanup."""
		frappe.delete_doc("Seller", self.seller.name)
		frappe.delete_doc("Mark", self.mark.name)
		frappe.delete_doc("Grade", self.grade.name)
		frappe.delete_doc("Estate", self.estate.name)
		frappe.delete_doc("Packing", self.packing.name)
