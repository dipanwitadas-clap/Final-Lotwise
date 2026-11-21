import frappe
from frappe.tests.utils import FrappeTestCase


class TestBroker(FrappeTestCase):
	def test_auction_requires_centre_and_supplier(self):
		"""Broker must have centre, centre code and supplier."""
		broker = frappe.get_doc(
			{
				"doctype": "Broker",
				"broker_name": "Test Auction Broker",
				"broker_short_name": "TAB",
			}
		)
		self.assertRaises(frappe.ValidationError, broker.insert)

	def test_broker_name_mandatory(self):
		"""Should require broker_name."""
		broker = frappe.get_doc({"doctype": "Broker"})
		self.assertRaises(frappe.ValidationError, broker.insert)
