# Copyright (c) 2026, BusinessThat.Works and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTeaPurchase(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("Auction Centre", "Test Siliguri TP"):
			frappe.get_doc(
				{
					"doctype": "Auction Centre",
					"auction_centre": "Test Siliguri TP",
					"auction_centre_code": "TSLGTP",
				}
			).insert(ignore_permissions=True)

	def test_autoname_matches_tea_lot_scheme(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tea Purchase",
				"acquisition_channel": "Auction",
				"auction_centre": "Test Siliguri TP",
				"season": 2026,
				"sale_no": 55,
				"lot_no": "JT0099",
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.assertEqual(doc.name, "TSLGTP-2026-55-JT0099")
