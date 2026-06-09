# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestSeller(IntegrationTestCase):
# 	"""
# 	Integration tests for Seller.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestSeller(FrappeTestCase):
	def test_seller_creation(self):
		"""Should create seller with name."""
		seller = frappe.get_doc({"doctype": "Seller", "seller_name": "Test Seller"}).insert()
		self.assertEqual(seller.seller_name, "Test Seller")
		frappe.delete_doc("Seller", seller.name)

	def test_seller_name_mandatory(self):
		"""Should require seller_name."""
		seller = frappe.get_doc({"doctype": "Seller"})
		self.assertRaises(frappe.ValidationError, seller.insert)
