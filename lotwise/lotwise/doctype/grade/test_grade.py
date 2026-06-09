# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestGrade(IntegrationTestCase):
# 	"""
# 	Integration tests for Grade.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestGrade(FrappeTestCase):
	def test_create_grade(self):
		"""Should create grade with code."""
		grade = frappe.get_doc(
			{"doctype": "Grade", "grade_code": "TEST_BOP", "description": "Test Broken Orange Pekoe"}
		).insert()
		self.assertEqual(grade.grade_code, "TEST_BOP")
		frappe.delete_doc("Grade", grade.name)

	def test_grade_code_mandatory(self):
		"""Should require grade_code."""
		grade = frappe.get_doc({"doctype": "Grade"})
		self.assertRaises(frappe.ValidationError, grade.insert)
