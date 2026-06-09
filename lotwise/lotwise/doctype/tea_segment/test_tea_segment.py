# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestTeaSegment(IntegrationTestCase):
# 	"""
# 	Integration tests for TeaSegment.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
# Copyright (c) 2026, BusinessThat.Works and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTeaSegment(FrappeTestCase):
	"""Test suite for Tea Segment doctype."""

	def test_mandatory_fields_enforced(self):
		"""Test: mandatory fields enforced."""
		# Should fail without segment_name
		segment = frappe.get_doc({"doctype": "Tea Segment", "rank": 1})
		self.assertRaises(frappe.ValidationError, segment.insert)

		# Should fail without rank
		segment = frappe.get_doc({"doctype": "Tea Segment", "segment_name": "Test"})
		self.assertRaises(frappe.ValidationError, segment.insert)

	def test_rank_ordering_works(self):
		"""Test: rank ordering works."""
		# Create segments with different ranks
		seg1 = frappe.get_doc({"doctype": "Tea Segment", "segment_name": "Low", "rank": 1}).insert()

		seg2 = frappe.get_doc({"doctype": "Tea Segment", "segment_name": "Medium", "rank": 2}).insert()

		seg3 = frappe.get_doc({"doctype": "Tea Segment", "segment_name": "High", "rank": 3}).insert()

		# Verify ordering by rank
		segments = frappe.get_list(
			"Tea Segment", filters=[["segment_name", "in", ["Low", "Medium", "High"]]], order_by="rank asc"
		)

		self.assertEqual(len(segments), 3)
		self.assertEqual(segments[0].name, "Low")
		self.assertEqual(segments[1].name, "Medium")
		self.assertEqual(segments[2].name, "High")

		# Cleanup
		for seg in [seg1, seg2, seg3]:
			frappe.delete_doc("Tea Segment", seg.name)
