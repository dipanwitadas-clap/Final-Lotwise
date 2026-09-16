# Copyright (c) 2026, BusinessThat.Works and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from lotwise.lotwise.doctype.tea_lot_image_import import tea_lot_image_import as mod

_FAKE_ITEM = {
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
	"ctc_no": "CTC 4",
	"remarks": "red 253; blue X",
}

_FAKE_PAGE = {
	"broker": "PARCON",
	"auction_centre": "SILIGURI",
	"sale_no": 27,
	"acquisition_channel": "Auction",
	"confidence": "high",
	"notes": "",
	"items": [_FAKE_ITEM],
}


class TestTeaLotImageImport(FrappeTestCase):
	def setUp(self):
		# The OCR text is upper-case ("PARCON" / "SILIGURI") while master records are
		# stored as typed by a user (e.g. "Siliguri") — relying on this to also cover
		# _resolve_master's case-insensitive lookup assumption.
		if not frappe.db.exists("Broker", "PARCON"):
			frappe.get_doc({"doctype": "Broker", "broker_name": "PARCON"}).insert(ignore_permissions=True)
		if not frappe.db.exists("Auction Centre", "Siliguri"):
			frappe.get_doc({"doctype": "Auction Centre", "auction_centre": "Siliguri"}).insert(
				ignore_permissions=True
			)

	def _make_doc(self, num_images=1):
		return frappe.get_doc(
			{
				"doctype": "Tea Lot Image Import",
				"source_images": [
					{"file_name": f"page-{i + 1}.jpg", "file_url": f"/files/page-{i + 1}.jpg"}
					for i in range(num_images)
				],
			}
		).insert()

	# ── _compute_totals ─────────────────────────────────────────────────

	def test_compute_totals(self):
		items = [
			{"pkgs": "20", "total_net": 100.5},
			{"pkgs": "15 / B7", "total_net": 50.25},
			{"pkgs": "", "total_net": 0},
		]
		packages, net = mod._compute_totals(items)
		self.assertEqual(packages, 35)
		self.assertAlmostEqual(net, 150.75, places=2)

	# ── _split_garden_region ─────────────────────────────────────────────

	def test_split_garden_region_splits_name_and_code(self):
		self.assertEqual(mod._split_garden_region("NOWERA NUDDY (DO)"), ("NOWERA NUDDY", "DO"))
		self.assertEqual(mod._split_garden_region("CHALOUNI (DO)"), ("CHALOUNI", "DO"))

	def test_split_garden_region_no_parens_leaves_region_empty(self):
		self.assertEqual(mod._split_garden_region("BARADIGHI"), ("BARADIGHI", ""))

	def test_split_garden_region_handles_blank_and_whitespace(self):
		self.assertEqual(mod._split_garden_region(""), ("", ""))
		self.assertEqual(mod._split_garden_region(None), ("", ""))
		self.assertEqual(mod._split_garden_region("  CHALOUNI   (  DO  )  "), ("CHALOUNI", "DO"))

	# ── _merge_pages ─────────────────────────────────────────────────────

	def test_merge_pages_carries_forward_and_dedupes(self):
		row = lambda **overrides: {  # noqa: E731
			"lot_inv_no": "",
			"chest_nos": "",
			"grade": "",
			"company": "",
			"garden": "",
			"warehouse": "",
			"ctc_no": "",
			"gr_wt": 1,
			"net_wt": 1,
			"total_net": 1,
			"pkgs": "1",
			"awr_dt": "",
			"gp_no_dt": "",
			"mfg_month_year": "",
			"location": "",
			"remarks": "",
			**overrides,
		}

		page1 = {
			"broker": "PARCON",
			"auction_centre": "SILIGURI",
			"sale_no": 27,
			"acquisition_channel": "Auction",
			"confidence": "high",
			"notes": "",
			"items": [
				row(
					lot_inv_no="55(C334)",
					chest_nos="4342/4361",
					grade="BOP",
					company="RYDAK",
					garden="BARADIGHI",
					warehouse="NTCL(63)",
					ctc_no="CTC 4",
				),
				# blank heading/grade — block continues onto page 2 without a repeated heading
				row(lot_inv_no="56(C335)", chest_nos="4362/4370"),
			],
		}
		page2 = {
			"broker": "",
			"auction_centre": "",
			"sale_no": 0,
			"acquisition_channel": "",
			"confidence": "medium",
			"notes": "",
			"items": [
				# duplicate of page1's last row, split across the page break
				row(lot_inv_no="56(C335)", chest_nos="4362/4370"),
				row(lot_inv_no="57(C336)", chest_nos="4371/4380"),
			],
		}

		merged = mod._merge_pages([page1, page2])

		self.assertEqual(merged["broker"], "PARCON")
		self.assertEqual(merged["auction_centre"], "SILIGURI")
		self.assertEqual(merged["confidence"], "medium")
		# the boundary duplicate collapses -> 3 unique lots, not 4
		self.assertEqual(len(merged["items"]), 3)
		# neither 56 nor 57 printed a heading/grade -> carried forward from row 1
		self.assertEqual(merged["items"][-1]["grade"], "BOP")
		self.assertEqual(merged["items"][-1]["company"], "RYDAK")

	# ── _apply_extraction ────────────────────────────────────────────────

	def test_apply_extraction_computes_totals_and_status(self):
		doc = self._make_doc()
		merged = {
			**{k: v for k, v in _FAKE_PAGE.items() if k != "items"},
			"items": [
				{**_FAKE_ITEM, "pkgs": "20", "total_net": 100.0},
				{**_FAKE_ITEM, "pkgs": "15", "total_net": 50.0},
			],
		}
		doc._apply_extraction(merged)
		self.assertEqual(doc.scan_status, "Scanned")
		self.assertEqual(doc.total_packages, 35)
		self.assertAlmostEqual(doc.total_net, 150.0, places=2)
		self.assertEqual(doc.broker, "PARCON")
		self.assertEqual(doc.auction_centre, "Siliguri")
		self.assertEqual(doc.scan_error, "")
		self.assertEqual(doc.items[0].garden, "BARADIGHI")
		self.assertEqual(doc.items[0].region, "DO")

	def test_apply_extraction_garden_without_region_leaves_region_blank(self):
		doc = self._make_doc()
		merged = {**_FAKE_PAGE, "items": [{**_FAKE_ITEM, "garden": "BARADIGHI"}]}
		doc._apply_extraction(merged)
		self.assertEqual(doc.items[0].garden, "BARADIGHI")
		self.assertEqual(doc.items[0].region, "")

	def test_apply_extraction_no_rows_is_error(self):
		doc = self._make_doc()
		doc._apply_extraction({**_FAKE_PAGE, "items": []})
		self.assertEqual(doc.scan_status, "Error")

	def test_apply_extraction_unresolved_broker_keeps_items(self):
		doc = self._make_doc()
		merged = {**_FAKE_PAGE, "broker": "UNKNOWN BROKER"}
		doc._apply_extraction(merged)
		self.assertEqual(doc.scan_status, "Error")
		self.assertIn("Broker", doc.scan_error)
		self.assertIn("UNKNOWN BROKER", doc.scan_error)
		self.assertFalse(doc.broker)
		doc.save()  # a Link field left empty must never raise LinkValidationError
		self.assertEqual(len(doc.items), 1)
		self.assertEqual(doc.total_packages, 20)

	def test_apply_extraction_unresolved_auction_centre_leaves_link_empty(self):
		doc = self._make_doc()
		merged = {**_FAKE_PAGE, "auction_centre": "NOWHERE"}
		doc._apply_extraction(merged)
		self.assertEqual(doc.scan_status, "Error")
		self.assertIn("Auction Centre", doc.scan_error)
		self.assertIn("NOWHERE", doc.scan_error)
		self.assertFalse(doc.auction_centre)
		doc.save()  # a Link field left empty must never raise LinkValidationError

	# ── scan_image() guards ──────────────────────────────────────────────

	def test_scan_image_without_api_key_throws(self):
		doc = self._make_doc()
		with patch.dict(frappe.conf, {}, clear=False):
			frappe.conf.pop("anthropic_api_key", None)
			self.assertRaises(frappe.ValidationError, mod.scan_image, doc.name)

	def test_scan_image_enqueues_and_returns_immediately(self):
		doc = self._make_doc()
		with (
			patch.object(frappe, "enqueue") as mock_enqueue,
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			result = mod.scan_image(doc.name)

		self.assertTrue(result["success"])
		self.assertEqual(result["total"], 1)
		mock_enqueue.assert_called_once()
		_, kwargs = mock_enqueue.call_args
		self.assertEqual(kwargs["job_id"], f"tea_lot_scan_{doc.name}")
		self.assertEqual(kwargs["queue"], "long")
		self.assertEqual(kwargs["doc_name"], doc.name)
		self.assertEqual(frappe.db.get_value(doc.doctype, doc.name, "scan_status"), "Processing")

	def test_scan_image_blocks_when_already_processing(self):
		doc = self._make_doc()
		frappe.db.set_value(doc.doctype, doc.name, "scan_status", "Processing")
		with patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False):
			self.assertRaises(frappe.ValidationError, mod.scan_image, doc.name)

	def test_scan_image_resets_source_rows_to_pending(self):
		doc = self._make_doc()
		frappe.db.set_value(doc.source_images[0].doctype, doc.source_images[0].name, "status", "Failed")
		frappe.db.set_value(doc.doctype, doc.name, "scan_error", "stale error from a previous run")
		with (
			patch.object(frappe, "enqueue"),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			mod.scan_image(doc.name)
		doc.reload()
		self.assertEqual(doc.source_images[0].status, "Pending")
		self.assertEqual(doc.scan_error, "")

	# ── process_tea_lot_scan (job body, called directly — the standard way
	#    to unit-test an RQ job without a real worker) ────────────────────

	def test_process_tea_lot_scan_end_to_end(self):
		doc = self._make_doc()
		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude_page", return_value=_FAKE_PAGE),
			patch.object(mod.frappe, "publish_realtime") as mock_publish,
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			mod.process_tea_lot_scan(doc.name)

		doc.reload()
		self.assertEqual(doc.scan_status, "Scanned")
		self.assertEqual(len(doc.items), 1)
		self.assertEqual(doc.broker, "PARCON")
		self.assertEqual(doc.auction_centre, "Siliguri")
		self.assertEqual(doc.total_packages, 20)
		self.assertAlmostEqual(doc.total_net, 691.40, places=2)
		self.assertEqual(doc.source_images[0].status, "Extracted")

		events = [call.args[0] for call in mock_publish.call_args_list]
		self.assertEqual(events, ["tea_scan_progress"] * len(events))
		phases = [call.args[1]["phase"] for call in mock_publish.call_args_list]
		self.assertIn("scanning", phases)
		self.assertIn("done", phases)

	def test_process_tea_lot_scan_always_unlocks_on_total_failure(self):
		doc = self._make_doc()
		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude_page", side_effect=ValueError("boom")),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			mod.process_tea_lot_scan(doc.name)

		self.assertEqual(frappe.db.get_value(doc.doctype, doc.name, "scan_status"), "Error")
		doc.reload()
		self.assertEqual(doc.source_images[0].status, "Failed")
		self.assertIn("boom", doc.source_images[0].error_msg)

	def test_process_tea_lot_scan_partial_page_failure(self):
		doc = self._make_doc(num_images=2)
		outcomes = [_FAKE_PAGE, ValueError("bad page")]

		def fake_call(api_key, model, image, page_no, total_pages):
			outcome = outcomes[page_no - 1]
			if isinstance(outcome, Exception):
				raise outcome
			return outcome

		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude_page", side_effect=fake_call),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			mod.process_tea_lot_scan(doc.name)

		doc.reload()
		self.assertEqual(doc.scan_status, "Partial")
		self.assertEqual(len(doc.items), 1)
		self.assertEqual(doc.source_images[0].status, "Extracted")
		self.assertEqual(doc.source_images[1].status, "Failed")
		self.assertIn("bad page", doc.source_images[1].error_msg)

	def test_process_tea_lot_scan_resolution_error_not_downgraded_to_partial(self):
		# A broker/auction-centre resolution failure must win over the "any page
		# failed -> Partial" downgrade in _do_scan, otherwise the real reason for
		# the Error status would be silently lost.
		doc = self._make_doc(num_images=2)
		outcomes = [{**_FAKE_PAGE, "broker": "UNKNOWN BROKER"}, ValueError("bad page")]

		def fake_call(api_key, model, image, page_no, total_pages):
			outcome = outcomes[page_no - 1]
			if isinstance(outcome, Exception):
				raise outcome
			return outcome

		with (
			patch.object(mod, "_load_image_b64", return_value=("ZmFrZQ==", "image/jpeg")),
			patch.object(mod, "_call_claude_page", side_effect=fake_call),
			patch.dict(frappe.conf, {"anthropic_api_key": "sk-test"}, clear=False),
		):
			mod.process_tea_lot_scan(doc.name)

		doc.reload()
		self.assertEqual(doc.scan_status, "Error")
		self.assertIn("Broker", doc.scan_error)
		self.assertEqual(len(doc.items), 1)

	# ── unlock_stale_scans ───────────────────────────────────────────────

	def test_unlock_stale_scans(self):
		doc = self._make_doc()
		frappe.db.set_value(doc.doctype, doc.name, "scan_status", "Processing")
		frappe.db.set_value(doc.source_images[0].doctype, doc.source_images[0].name, "status", "Processing")
		stale_time = add_to_date(now_datetime(), minutes=-45)
		frappe.db.set_value(doc.doctype, doc.name, "modified", stale_time, update_modified=False)
		frappe.db.commit()

		with patch.object(mod.frappe, "publish_realtime") as mock_publish:
			mod.unlock_stale_scans()

		self.assertEqual(frappe.db.get_value(doc.doctype, doc.name, "scan_status"), "Error")
		doc.reload()
		self.assertEqual(doc.source_images[0].status, "Failed")
		mock_publish.assert_called()
