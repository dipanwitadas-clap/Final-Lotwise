# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestPacking(IntegrationTestCase):
# 	"""
# 	Integration tests for Packing.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestPacking(FrappeTestCase):
	def test_create_packing(self):
		"""Should create packing with code."""
		packing = frappe.get_doc(
			{"doctype": "Packing", "packing_code": "TEST_PS", "description": "Test Paper Sack"}
		).insert()
		self.assertEqual(packing.packing_code, "TEST_PS")
		frappe.delete_doc("Packing", packing.name)

	def test_packing_code_mandatory(self):
		"""Should require packing_code."""
		packing = frappe.get_doc({"doctype": "Packing"})
		self.assertRaises(frappe.ValidationError, packing.insert)
