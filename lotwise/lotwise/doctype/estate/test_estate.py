# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestEstate(IntegrationTestCase):
# 	"""
# 	Integration tests for Estate.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
# Copyright (c) 2026, BusinessThat.Works
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestEstate(FrappeTestCase):
	"""Test suite for Estate doctype."""

	def test_create_estate(self):
		"""Should create estate with name and region."""
		estate = frappe.get_doc(
			{"doctype": "Estate", "estate_name": "Test Gelakey", "region": "Assam"}
		).insert()

		self.assertEqual(estate.estate_name, "Test Gelakey")
		self.assertEqual(estate.region, "Assam")
		self.assertEqual(estate.name, "Test Gelakey")

		frappe.delete_doc("Estate", estate.name)

	def test_estate_name_mandatory(self):
		"""Should reject estate without name."""
		estate = frappe.get_doc({"doctype": "Estate", "region": "Assam"})
		self.assertRaises(frappe.ValidationError, estate.insert)
