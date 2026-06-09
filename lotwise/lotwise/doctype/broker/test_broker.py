# # Copyright (c) 2026, BusinessThat.Works and Contributors
# # See license.txt

# # import frappe
# from frappe.tests import IntegrationTestCase


# # On IntegrationTestCase, the doctype test records and all
# # link-field test record dependencies are recursively loaded
# # Use these module variables to add/remove to/from that list
# EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


# class IntegrationTestBroker(IntegrationTestCase):
# 	"""
# 	Integration tests for Broker.
# 	Use this class for testing interactions between multiple components.
# 	"""

# 	pass
import frappe
from frappe.tests.utils import FrappeTestCase


class TestBroker(FrappeTestCase):
	def test_broker_creation(self):
		"""Should create broker with name and centre."""
		broker = frappe.get_doc(
			{"doctype": "Broker", "broker_name": "Test Parcon", "centre": "Guwahati"}
		).insert()
		self.assertEqual(broker.broker_name, "Test Parcon")
		frappe.delete_doc("Broker", broker.name)

	def test_broker_name_mandatory(self):
		"""Should require broker_name."""
		broker = frappe.get_doc({"doctype": "Broker"})
		self.assertRaises(frappe.ValidationError, broker.insert)
