import frappe
from frappe.tests.utils import FrappeTestCase


class TestBroker(FrappeTestCase):
	def test_private_broker_name(self):
		"""Private broker is named <broker_name>-PVT without centre/supplier."""
		broker = frappe.get_doc(
			{
				"doctype": "Broker",
				"broker_name": "Test Pvt Broker",
				"broker_short_name": "TPB",
				"acquisition_channel": "Private",
			}
		).insert()
		self.assertEqual(broker.name, "Test Pvt Broker-PVT")
		frappe.delete_doc("Broker", broker.name)

	def test_auction_requires_centre_and_supplier(self):
		"""Auction broker must have centre, centre code and supplier."""
		broker = frappe.get_doc(
			{
				"doctype": "Broker",
				"broker_name": "Test Auction Broker",
				"broker_short_name": "TAB",
				"acquisition_channel": "Auction",
			}
		)
		self.assertRaises(frappe.ValidationError, broker.insert)

	def test_broker_name_mandatory(self):
		"""Should require broker_name."""
		broker = frappe.get_doc({"doctype": "Broker"})
		self.assertRaises(frappe.ValidationError, broker.insert)
