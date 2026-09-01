# Copyright (c) 2026, BusinessThat.Works and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lotwise.lotwise.doctype.tea_lot_image_import import tea_lot_image_import as mod

_FAKE_EXTRACTION = {
	"broker": "PARCON SILIGURI",
	"series": "CTC 4",
	"sale_no": 27,
	"acquisition_channel": "Auction",
	"total_packages": 370,
	"total_net": 13482.20,
	"confidence": "high",
	"notes": "",
	"items": [
		{
			"lot_inv_no": "55(C334)",
			"grade": "BOP",
			"chest_nos": "4342 / 4361",
			"gr_wt": 35.20,
			"net_wt": 35.00,
			"total_net": 691.40,
			"pkgs": "20",
			"awr_dt": "13/06/2026",
			"gp_no_dt": "19-12/06/2026",
			"mfg_month_year": "Jun-26",
			"location": "",
			"garden": "BARADIGHI (DO)",
			"company": "RYDAK SYNDICATE LIMITED",
			"warehouse": "NTCL(63)",
			"remarks": "red 253; blue X",
		}
	],
}


class TestTeaLotImageImport(FrappeTestCase):
	def _make_doc(self):
		return frappe.get_doc(
			{
				"doctype": "Tea Lot Image Import",
				"source_image": "/files/does-not-matter.jpg",
			}
		).insert()

	def test_scan_image_populates_header_and_items(self):
		doc = self._make_doc()
		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude", return_value=_FAKE_EXTRACTION),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			result = doc.scan_image()

		self.assertEqual(result["rows"], 1)
		self.assertEqual(doc.scan_status, "Scanned")
		self.assertEqual(doc.broker, "PARCON SILIGURI")
		self.assertEqual(doc.series, "CTC 4")
		self.assertEqual(doc.sale_no, 27)
		self.assertEqual(doc.total_packages, 370)
		self.assertAlmostEqual(doc.total_net, 13482.20, places=2)

		row = doc.items[0]
		self.assertEqual(row.lot_inv_no, "55(C334)")
		self.assertEqual(row.grade, "BOP")
		self.assertAlmostEqual(row.gr_wt, 35.20, places=2)
		self.assertAlmostEqual(row.total_net, 691.40, places=2)
		self.assertEqual(str(row.awr_dt), "2026-06-13")
		self.assertEqual(row.company, "RYDAK SYNDICATE LIMITED")
		self.assertIn("253", row.remarks)

	def test_scan_image_without_api_key_throws(self):
		doc = self._make_doc()
		with patch.dict(frappe.conf, {}, clear=False):
			frappe.conf.pop("anthropic_api_key", None)
			self.assertRaises(frappe.ValidationError, doc.scan_image)

	def test_low_confidence_marks_partial(self):
		doc = self._make_doc()
		payload = {**_FAKE_EXTRACTION, "confidence": "low"}
		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude", return_value=payload),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			doc.scan_image()
		self.assertEqual(doc.scan_status, "Partial")
