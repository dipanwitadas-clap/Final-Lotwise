# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestMark(IntegrationTestCase):
# 	"""
# 	Integration tests for Mark.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
# Copyright (c) 2026, BusinessThat.Works
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMark(FrappeTestCase):
	"""Test suite for Mark doctype."""

	def setUp(self):
		"""Create test dependencies."""
		self.estate = frappe.get_doc(
			{"doctype": "Estate", "estate_name": "Test Estate Mark", "region": "Assam"}
		).insert()

		self.segment = frappe.get_doc(
			{"doctype": "Tea Segment", "segment_name": "Test Segment Mark", "rank": 2}
		).insert()

	def test_mark_requires_estate(self):
		"""Mark should require estate."""
		mark = frappe.get_doc({"doctype": "Mark", "mark_name": "Test Mark No Estate"})
		self.assertRaises(frappe.ValidationError, mark.insert)

	def test_create_mark_with_estate(self):
		"""Should create mark with estate."""
		mark = frappe.get_doc(
			{
				"doctype": "Mark",
				"mark_name": "Test Gelakey Mark",
				"estate": self.estate.name,
				"default_segment": self.segment.name,
				"certification": "Test Certified",
			}
		).insert()

		self.assertEqual(mark.mark_name, "Test Gelakey Mark")
		self.assertEqual(mark.estate, self.estate.name)
		self.assertEqual(mark.default_segment, self.segment.name)

		frappe.delete_doc("Mark", mark.name)

	def tearDown(self):
		"""Cleanup test data."""
		frappe.delete_doc("Estate", self.estate.name)
		frappe.delete_doc("Tea Segment", self.segment.name)
