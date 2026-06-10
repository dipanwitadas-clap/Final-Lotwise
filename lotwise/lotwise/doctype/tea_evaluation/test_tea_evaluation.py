# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestTeaEvaluation(IntegrationTestCase):
# 	"""
# 	Integration tests for TeaEvaluation.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestTeaEvaluation(FrappeTestCase):
	def setUp(self):
		"""Create test dependencies."""
		self.seller = frappe.get_doc({"doctype": "Seller", "seller_name": "Test Seller Eval"}).insert()

		self.estate = frappe.get_doc({"doctype": "Estate", "estate_name": "Test Estate Eval"}).insert()

		self.mark = frappe.get_doc(
			{"doctype": "Mark", "mark_name": "Test Mark Eval", "estate": self.estate.name}
		).insert()

		self.grade = frappe.get_doc(
			{"doctype": "Grade", "grade_code": "BOP_EVAL", "description": "Test"}
		).insert()

		self.packing = frappe.get_doc(
			{"doctype": "Packing", "packing_code": "TEST_EVAL", "description": "Test"}
		).insert()

		self.taster = frappe.get_doc({"doctype": "Taster", "taster_name": "Test Taster"}).insert()

		self.tea_lot = frappe.get_doc(
			{
				"doctype": "Tea Lot",
				"acquisition_channel": "Private",
				"seller": self.seller.name,
				"mark": self.mark.name,
				"grade": self.grade.name,
				"invoice_number": "INV-EVAL",
				"packing": self.packing.name,
				"packages": 20,
				"net_weight_total": 595.70,
			}
		).insert()

	def test_create_evaluation(self):
		"""Should create evaluation with sensory scores."""
		eval_doc = frappe.get_doc(
			{
				"doctype": "Tea Evaluation",
				"tea_lot": self.tea_lot.name,
				"taster": self.taster.name,
				"stage": "Pre-purchase",
				"evaluation_date": "2026-06-10",
				"colour": 8.0,
				"strength": 8.5,
				"taste": 8.2,
				"briskness": 7.8,
				"suggested_valuation": 150.00,
				"notes": "Good quality tea",
			}
		).insert()

		self.assertEqual(eval_doc.stage, "Pre-purchase")
		self.assertEqual(eval_doc.taste, 8.2)
		frappe.delete_doc("Tea Evaluation", eval_doc.name)

	def test_mandatory_fields_enforced(self):
		"""Should require tea_lot, taster, stage."""
		eval_doc = frappe.get_doc({"doctype": "Tea Evaluation", "colour": 8.0})
		self.assertRaises(frappe.ValidationError, eval_doc.insert)

	def tearDown(self):
		"""Cleanup."""
		frappe.delete_doc("Tea Lot", self.tea_lot.name)
		frappe.delete_doc("Seller", self.seller.name)
		frappe.delete_doc("Mark", self.mark.name)
		frappe.delete_doc("Grade", self.grade.name)
		frappe.delete_doc("Estate", self.estate.name)
		frappe.delete_doc("Packing", self.packing.name)
		frappe.delete_doc("Taster", self.taster.name)
