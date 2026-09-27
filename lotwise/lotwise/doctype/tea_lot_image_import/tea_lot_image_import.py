# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import concurrent.futures
import io
import json
import re
from datetime import date, datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, flt, now_datetime

DEFAULT_MODEL = "claude-sonnet-5"
MAX_IMAGE_EDGE = 1568
MAX_WORKERS = 5
STALE_SCAN_THRESHOLD_MINUTES = 30

CHILD_DOCTYPE = "Tea Lot Image Import Source"

# Child-table columns filled verbatim from the extracted JSON (strings).
_TEXT_FIELDS = (
	"lot_inv_no",
	"grade",
	"chest_nos",
	"gp_no_dt",
	"mfg_month_year",
	"location",
	"pkgs",
	"garden",
	"company",
	"warehouse",
	"ctc_no",
	"remarks",
)
# Child-table columns coerced to Float.
_NUM_FIELDS = ("gr_wt", "net_wt", "total_net")

# Header/group fields carried forward across blank cells and page boundaries in _merge_pages.
_CARRY_FIELDS = ("grade", "company", "garden", "warehouse", "ctc_no")

_VALID_CHANNELS = ("Auction", "Private", "Outsourced")

_ITEM_SCHEMA = {
	"type": "object",
	"properties": {
		"lot_inv_no": {"type": "string", "description": "LOT INV NO cell, e.g. '55(C334)'"},
		"grade": {"type": "string", "description": "GRADE; inherit the last printed grade when blank"},
		"chest_nos": {"type": "string", "description": "CHEST NOS range, e.g. '4342 / 4361'"},
		"gr_wt": {"type": "number", "description": "GR. WT.; 0 if absent"},
		"net_wt": {"type": "number", "description": "NET WT.; 0 if absent"},
		"total_net": {"type": "number", "description": "TOTAL NET for the row; 0 if absent"},
		"pkgs": {"type": "string", "description": "PKGS value incl. any sub-code, e.g. '20 / B7'"},
		"awr_dt": {"type": "string", "description": "AWR DT as dd/mm/yyyy, or '' if absent"},
		"gp_no_dt": {"type": "string", "description": "GP NO / DT text, e.g. '19-12/06/2026'"},
		"mfg_month_year": {"type": "string", "description": "MFG MONTH/YEAR, e.g. 'Jun-26'"},
		"location": {"type": "string", "description": "LOCATION cell text"},
		"garden": {"type": "string", "description": "Garden / estate from the group heading"},
		"company": {"type": "string", "description": "Company / producer from the group heading"},
		"warehouse": {"type": "string", "description": "Warehouse code, e.g. 'NTCL(63)'"},
		"ctc_no": {
			"type": "string",
			"description": (
				"Series / CTC No from the page header (e.g. 'CTC 4'); apply it to every row "
				"unless a different value is explicitly printed for that row. '' if absent."
			),
		},
		"remarks": {
			"type": "string",
			"description": (
				"All handwritten annotations near this row: red valuation numbers and "
				"blue bid prices / status like '295 B', '300 B7', 'OUT', 'X'. "
				"Format e.g. 'red 253; blue 295 B'. '' if none."
			),
		},
	},
	"required": [
		"lot_inv_no",
		"grade",
		"chest_nos",
		"gr_wt",
		"net_wt",
		"total_net",
		"pkgs",
		"awr_dt",
		"gp_no_dt",
		"mfg_month_year",
		"location",
		"garden",
		"company",
		"warehouse",
		"ctc_no",
		"remarks",
	],
	"additionalProperties": False,
}

# Schema for a SINGLE page call — no cross-page totals. total_packages/total_net are
# computed in Python from the merged item rows, never asked of the model (see
# _compute_totals): summary lines are easy to misread and cross-page arithmetic is
# an unnecessary source of error.
_PAGE_SCHEMA = {
	"type": "object",
	"properties": {
		"broker": {
			"type": "string",
			"description": (
				"Broker / auctioneer's own name from the header strip, e.g. 'PARCON', "
				"'J THOMAS', 'PARAMOUNT TEA BROKER' — may be one or several words. Do NOT "
				"include the auction centre city. '' if the header strip is not on this page."
			),
		},
		"auction_centre": {
			"type": "string",
			"description": (
				"Auction centre city from the header strip, printed immediately after the "
				"broker name, e.g. 'SILIGURI', 'GUWAHATI', 'KOLKATA' — always a single word. "
				"'' if the header strip is not on this page."
			),
		},
		"sale_no": {"type": "integer", "description": "Sale No; 0 if absent"},
		"acquisition_channel": {
			"type": "string",
			"enum": ["Auction", "Private", "Outsourced", ""],
			"description": "Infer from wording; '' if unclear",
		},
		"confidence": {
			"type": "string",
			"enum": ["high", "medium", "low"],
			"description": "Confidence that every row on this page was read correctly",
		},
		"notes": {
			"type": "string",
			"description": "Anything ambiguous or unreadable on this page; '' if none",
		},
		"items": {"type": "array", "items": _ITEM_SCHEMA},
	},
	"required": [
		"broker",
		"auction_centre",
		"sale_no",
		"acquisition_channel",
		"confidence",
		"notes",
		"items",
	],
	"additionalProperties": False,
}

_SYSTEM_PROMPT = (
	"You transcribe scanned Indian tea-auction broker catalogue pages into structured data. "
	"Read every printed lot line and every handwritten annotation exactly as written. "
	"Never invent values: use an empty string or 0 for anything you cannot read."
)

# Static (no per-page substitution) so it's identical across every page call and can be
# prompt-cached — page numbering is carried in the small text block sent alongside it.
_USER_PROMPT_PAGE = """This image is one page of a tea-auction broker's printed lot catalogue, with
handwritten marks added by hand. You cannot see any other page — extract only what is printed or
written on this page into `items`.

Printed table columns (left to right): LOT INV NO, GRADE, CHEST NOS, GR. WT, NET WT, TOTAL NET,
PKGS, AWR DT, GP NO/DT, MFG MONTH/YEAR, LOCATION.

Structure:
- Bold centred lines above a block of rows give the COMPANY (e.g. "RYDAK SYNDICATE LIMITED"),
  then the GARDEN / estate (e.g. "BARADIGHI (DO)"). A code such as "NTCL(63)" or
  "KTTWPL - UNIT - 1(39)" is the WAREHOUSE. Apply the current company / garden / warehouse to
  every row until the heading changes on this page.
- When a GRADE cell is blank, carry down the last printed grade seen so far ON THIS PAGE.
- If the rows at the very top of this page have no heading or grade printed above them —
  because the block continues from a previous page you cannot see — leave grade, garden,
  company, and warehouse EMPTY for those rows rather than guessing. A later step carries the
  correct values forward from the previous page automatically.
- Each printed lot line on this page is one entry in `items`, even if it looks like it
  continues onto the next page.
- Ignore this page's own "Total :" summary line; do not attempt to sum anything — totals are
  computed separately from the extracted rows.

Handwritten marks:
- Red numbers next to a row = internal valuation.
- Blue text like "295 B", "300 B7", "OUT", "X" = bid price / status.
- Put every handwritten mark for a row into that row's `remarks` (e.g. "red 253; blue 295 B").
- Keep rows marked "OUT"; set their `remarks` to include "OUT".

If a header strip appears on this page, it prints the broker's name immediately followed by
the auction centre city as one run of text, e.g. "PARCON SILIGURI" (broker "PARCON", auction
centre "SILIGURI") or "PARAMOUNT TEA BROKER GUWAHATI" (broker "PARAMOUNT TEA BROKER", auction
centre "GUWAHATI"). The broker name may be one or several words; the auction centre is always
the single word at the end, a city name. Use your knowledge of real Indian tea-broker names to
decide where the broker name ends and the city begins, rather than assuming it is always just
the last word. Fill `broker` and `auction_centre` separately. The same strip also carries the
series / CTC No (e.g. "CTC 4") and "Sale No : NN": fill `sale_no` and apply that series / CTC
No to every row's `ctc_no` unless a row explicitly prints a different one. Otherwise leave
`broker`, `auction_centre`, and `sale_no` empty — the caller applies the value from whichever
page has it.

Extract this page now."""


def _resolve_master(doctype: str, value: str, label: str) -> tuple[str | None, str | None]:
	"""Resolve `value` to an existing `doctype` docname. Both Broker and Auction Centre
	are autonamed by their own identifying field, so the extracted text IS the docname to
	look up. Returns (canonical_name, None) on success or (None, message) using the same
	"'<value>' not found. Please create it first." phrasing Tea Lot Import already uses
	for Mark/Grade/Warehouse."""
	value = (value or "").strip()
	if not value:
		return None, None
	canonical = frappe.db.get_value(doctype, value, "name")
	if canonical:
		return canonical, None
	return None, _("{0} '{1}' not found. Please create it first.").format(label, value)


_LOT_INV_NO_RE = re.compile(r"^\s*(\d+)\s*\(\s*([^)]*)\s*\)\s*$")


def _parse_lot_inv_no(value: str) -> tuple[str | None, str | None]:
	"""'201(C517)' -> ('201', 'C517'). Falls back to treating the whole
	(trimmed) string as the lot number, with no invoice number, when it
	doesn't match the expected 'NNN(code)' shape."""
	value = (value or "").strip()
	if not value:
		return None, None
	match = _LOT_INV_NO_RE.match(value)
	if match:
		return match.group(1), match.group(2).strip() or None
	return value, None


_GARDEN_REGION_RE = re.compile(r"^\s*(.*?)\s*\(\s*([^()]*)\s*\)\s*$")


def _split_garden_region(value: str) -> tuple[str, str]:
	"""'NOWERA NUDDY (DO)' -> ('NOWERA NUDDY', 'DO'). Falls back to treating the
	whole (trimmed) string as the garden/mark name, with an empty region, when
	it doesn't match the expected 'NAME (CODE)' shape."""
	value = (value or "").strip()
	if not value:
		return "", ""
	match = _GARDEN_REGION_RE.match(value)
	if not match:
		return value, ""
	return match.group(1).strip(), match.group(2).strip()


class TeaLotImageImport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.tea_lot_image_import_item.tea_lot_image_import_item import (
			TeaLotImageImportItem,
		)
		from lotwise.lotwise.doctype.tea_lot_image_import_source.tea_lot_image_import_source import (
			TeaLotImageImportSource,
		)

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		auction_centre_code: DF.Data | None
		broker: DF.Link | None
		broker_short_name: DF.Data | None
		fiscal_year: DF.Link
		items: DF.Table[TeaLotImageImportItem]
		offer_date: DF.Date | None
		processed_pages: DF.Int
		purchase_status: DF.Link | None
		sale_no: DF.Int
		scan_error: DF.SmallText | None
		scan_status: DF.Literal["Not Scanned", "Processing", "Scanned", "Partial", "Error"]
		season: DF.Int
		source_images: DF.Table[TeaLotImageImportSource]
		total_net: DF.Float
		total_packages: DF.Int
		total_pages: DF.Int
	# end: auto-generated types

	def validate(self):
		# The background job updates progress via frappe.db.set_value (bypasses this
		# hook entirely), and by the time it calls doc.save() at the end,
		# _apply_extraction has already moved scan_status off "Processing" — so this
		# only ever blocks a stray user save while a scan is running, never the
		# job's own final save.
		if self.scan_status == "Processing":
			frappe.throw(_("A scan is already in progress. Please wait until it completes."))

	def _apply_extraction(self, data: dict) -> None:
		"""Map the merged extraction JSON onto the document. Header fields are only
		set when empty (so a user can pre-fill them); items and totals (computed
		here from the extracted rows, never trusted from the model) are always
		replaced. broker/auction_centre are only accepted if they resolve to an
		existing Broker / Auction Centre record — both are Link fields, so an
		unresolved value would abort doc.save() outright. A resolution failure is
		recorded in scan_error and forces scan_status to "Error", but items/totals
		are still applied and saved — the per-page Claude calls are never thrown
		away."""
		errors: list[str] = []

		if not self.broker and data.get("broker"):
			resolved, err = _resolve_master("Broker", data["broker"], _("Broker"))
			if err:
				errors.append(err)
			elif resolved:
				self.broker = resolved

		if not self.auction_centre and data.get("auction_centre"):
			resolved, err = _resolve_master("Auction Centre", data["auction_centre"], _("Auction Centre"))
			if err:
				errors.append(err)
			elif resolved:
				self.auction_centre = resolved

		if not self.sale_no and data.get("sale_no"):
			self.sale_no = cint(data["sale_no"])
		if not self.acquisition_channel and data.get("acquisition_channel") in _VALID_CHANNELS:
			self.acquisition_channel = data["acquisition_channel"]

		rows = data.get("items") or []
		self.set("items", [])
		for row in rows:
			values = {field: (row.get(field) or "") for field in _TEXT_FIELDS}
			for field in _NUM_FIELDS:
				raw = row.get(field)
				values[field] = flt(raw) if raw not in (None, "") else 0
			values["awr_dt"] = _parse_date(row.get("awr_dt"))
			values["garden"], values["region"] = _split_garden_region(values["garden"])
			self.append("items", values)

		self.total_packages, self.total_net = _compute_totals(rows)
		self.scan_error = " | ".join(errors)

		confidence = (data.get("confidence") or "").lower()
		if errors or not rows:
			self.scan_status = "Error"
		elif confidence == "high":
			self.scan_status = "Scanned"
		else:
			self.scan_status = "Partial"

	@frappe.whitelist()
	def create_tea_lots(self):
		"""Create one Tea Lot per Pending/Error/Duplicate row (Auction/Outsourced only).
		Mirrors TeaLotImport.create_tea_lots: per-row try/except, row_status/message/
		tea_lot tracking on the child row, and a {created, errors, duplicates} summary."""
		if self.acquisition_channel not in ("Auction", "Outsourced"):
			frappe.throw(_("Tea Lot creation is currently supported only for Auction/Outsourced."))
		if not self.auction_centre:
			frappe.throw(_("Auction Centre is required."))
		if not self.sale_no:
			frappe.throw(_("Sale No is required."))
		if not self.season:
			frappe.throw(_("Season is required."))
		if not self.fiscal_year:
			frappe.throw(_("Fiscal Year is required."))

		auction_centre_code = frappe.db.get_value(
			"Auction Centre", self.auction_centre, "auction_centre_code"
		)
		if not auction_centre_code:
			frappe.throw(_("Auction Centre Code not found."))

		is_offer = self.purchase_status == "Offer"
		if is_offer and not self.offer_date:
			frappe.throw(_("Offer Date is required."))

		meta = frappe.get_meta("Tea Lot")
		created = duplicate = error = 0

		for row in self.items:
			if row.row_status == "Created":
				continue
			try:
				lot_num, invoice_part = _parse_lot_inv_no(row.lot_inv_no)
				if not lot_num:
					row.row_status = "Error"
					row.message = _("Lot Inv No is missing or could not be parsed.")
					error += 1
					continue

				lot_no = f"{self.broker_short_name or ''}{lot_num}"

				resolved_mark, err = _resolve_master("Mark", row.garden, _("Mark"))
				if err:
					row.row_status = "Error"
					row.message = err
					error += 1
					continue

				if not is_offer and not row.purchase_date:
					row.row_status = "Error"
					row.message = _("Purchase Date is required for this row.")
					error += 1
					continue

				tea_lot_name = f"{auction_centre_code}-{self.season}-{self.sale_no}-{lot_no}"
				if frappe.db.exists("Tea Lot", tea_lot_name):
					row.row_status = "Duplicate"
					row.message = _("Tea Lot '{0}' already exists.").format(tea_lot_name)
					duplicate += 1
					continue

				values = {
					"doctype": "Tea Lot",
					"acquisition_channel": self.acquisition_channel,
					"purchase_status": self.purchase_status,
					"auction_centre": self.auction_centre,
					"grade": row.grade if row.grade else None,
					"broker": self.broker,
					"sale_no": self.sale_no,
					"season": self.season,
					"lot_no": lot_no,
					"invoice_number": invoice_part,
					"mark": resolved_mark,
					"fiscal_year": self.fiscal_year,
					"offer_date": self.offer_date if is_offer else None,
					"purchase_date": row.purchase_date if not is_offer else None,
					"source_doctype": self.doctype,
					"source_doctype_id": self.name,
				}
				values = {k: v for k, v in values.items() if k == "doctype" or meta.has_field(k)}

				lot = frappe.get_doc(values)
				lot.insert(ignore_permissions=True)

				row.tea_lot = lot.name
				row.row_status = "Created"
				row.message = _("Created {0}").format(lot.name)
				created += 1

			except Exception as e:
				row.row_status = "Error"
				row.message = str(e)[:140]
				error += 1
				frappe.log_error(frappe.get_traceback(), "Tea Lot Image Import: create_tea_lots row failed")

		self.save()
		return {"created": created, "errors": error, "duplicates": duplicate}


# ─────────────────────────────────────────────────────────────────────────
# ENTRY POINT — plain whitelisted function (not a Document method), so the
# server always reads current DB state via a fresh frappe.get_doc rather than
# whatever doc snapshot the client last had. Mirrors Fleet Bulk Upload's
# start_fleet_extraction(doc_name).
# ─────────────────────────────────────────────────────────────────────────


@frappe.whitelist()
def scan_image(doc_name: str) -> dict:
	"""Step 1 — validates, then enqueues the background scan job."""
	frappe.has_permission("Tea Lot Image Import", ptype="write", doc=doc_name, throw=True)
	doc = frappe.get_doc("Tea Lot Image Import", doc_name)

	if not doc.source_images:
		frappe.throw(_("Attach at least one source image before scanning."))
	if not frappe.conf.get("anthropic_api_key"):
		frappe.throw(
			_(
				"Anthropic API key is not configured. Add 'anthropic_api_key' to the site config "
				"(bench set-config anthropic_api_key ... / Frappe Cloud site Config)."
			)
		)
	if doc.scan_status == "Processing":
		frappe.throw(_("A scan is already in progress. Please wait until it completes."))

	total = len(doc.source_images)

	# Every scan re-sends every page (no incremental "retry only failed pages" —
	# that would need each page's own extracted JSON persisted), so reset every
	# row to Pending up front.
	files = frappe.qb.DocType(CHILD_DOCTYPE)
	frappe.qb.update(files).set(files.status, "Pending").set(files.error_msg, "").where(
		files.parent == doc_name
	).run()

	frappe.db.set_value(
		doc.doctype,
		doc.name,
		{"scan_status": "Processing", "total_pages": total, "processed_pages": 0, "scan_error": ""},
	)

	frappe.enqueue(
		"lotwise.lotwise.doctype.tea_lot_image_import.tea_lot_image_import.process_tea_lot_scan",
		queue="long",
		timeout=1500,
		job_id=f"tea_lot_scan_{doc_name}",
		deduplicate=False,
		enqueue_after_commit=True,
		doc_name=doc_name,
	)

	return {
		"success": True,
		"total": total,
		"message": _("{0} page(s) queued for scanning").format(total),
	}


# ─────────────────────────────────────────────────────────────────────────
# BACKGROUND JOB
# ─────────────────────────────────────────────────────────────────────────


def process_tea_lot_scan(doc_name: str) -> None:
	"""Job entry point (runs on the `long` queue). Delegates to _do_scan and
	ALWAYS finalizes via `finally`, so scan_status can never stay stuck on
	"Processing" for any exception raised inside the job (a hard-killed worker
	process is a separate case — see unlock_stale_scans)."""
	try:
		_do_scan(doc_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Tea Lot Image Import: scan failed")
	finally:
		_finalize_scan_run(doc_name)


def _do_scan(doc_name: str) -> None:
	doctype = "Tea Lot Image Import"
	doc = frappe.get_doc(doctype, doc_name)
	api_key = frappe.conf.get("anthropic_api_key")
	if not api_key:
		raise ValueError(str(_("Anthropic API key is not configured.")))
	model = frappe.conf.get("anthropic_model") or DEFAULT_MODEL

	total = len(doc.source_images)
	row_names = [r.name for r in doc.source_images]
	file_names = [r.file_name for r in doc.source_images]

	files = frappe.qb.DocType(CHILD_DOCTYPE)
	frappe.qb.update(files).set(files.status, "Processing").where(files.parent == doc_name).run()
	frappe.db.commit()

	# Sequential, not parallel: _load_image_b64 calls frappe.get_doc("File", ...),
	# which touches frappe.local.db. frappe.local is contextvars-backed and is NOT
	# propagated into threads spawned by ThreadPoolExecutor, so running this inside
	# the pool below would crash every worker thread. It's local disk I/O + a PIL
	# resize anyway — not the bottleneck; only the Claude calls need to be parallel.
	images = [_load_image_b64(r.file_url) for r in doc.source_images]

	pages: list[dict | None] = [None] * total
	processed = 0

	def notify(current_file: str = "") -> None:
		frappe.publish_realtime(
			"tea_scan_progress",
			{
				"docname": doc_name,
				"processed": processed,
				"total": total,
				"current_file": current_file,
				"phase": "scanning",
			},
			doctype=doctype,
			docname=doc_name,
		)

	notify()
	with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, MAX_WORKERS)) as pool:
		future_map = {
			pool.submit(_call_claude_page, api_key, model, image, i + 1, total): i
			for i, image in enumerate(images)
		}
		for future in concurrent.futures.as_completed(future_map):
			i = future_map[future]
			try:
				pages[i] = future.result()
				frappe.db.set_value(CHILD_DOCTYPE, row_names[i], "status", "Extracted")
			except Exception as exc:
				frappe.db.set_value(CHILD_DOCTYPE, row_names[i], {"status": "Failed", "error_msg": str(exc)})
			processed += 1
			frappe.db.set_value(doctype, doc_name, "processed_pages", processed)
			frappe.db.commit()
			notify(file_names[i] if i < len(file_names) else "")

	good_pages = [p for p in pages if p is not None]
	if not good_pages:
		raise RuntimeError("Claude returned no data for any page.")

	merged = _merge_pages(good_pages)
	doc.reload()
	doc._apply_extraction(merged)
	if doc.scan_status != "Error" and any(r.status == "Failed" for r in doc.source_images):
		doc.scan_status = "Partial"
	doc.save()
	frappe.db.commit()


def _finalize_scan_run(doc_name: str) -> None:
	"""Runs from `finally` — always fires, whether _do_scan succeeded, a page
	failed, or an unexpected exception hit before any per-row update landed.
	The sole place that forces scan_status off "Processing" and unconditionally
	publishes the terminal realtime event, so the document never stays locked."""
	doctype = "Tea Lot Image Import"
	try:
		status = frappe.db.get_value(doctype, doc_name, "scan_status")
		if status == "Processing":
			# _do_scan never reached doc.save() — record the failure.
			frappe.db.set_value(doctype, doc_name, "scan_status", "Error", update_modified=True)
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Tea Lot Image Import: finalize failed")

	processed, total, status, scan_error = frappe.db.get_value(
		doctype, doc_name, ["processed_pages", "total_pages", "scan_status", "scan_error"]
	) or (0, 0, "Error", "")

	frappe.publish_realtime(
		"tea_scan_progress",
		{
			"docname": doc_name,
			"processed": processed or 0,
			"total": total or 0,
			"phase": "done",
			"status": status,
			"scan_error": scan_error or "",
		},
		doctype=doctype,
		docname=doc_name,
	)


def unlock_stale_scans() -> None:
	"""Hourly scheduled task (see hooks.py). `_finalize_scan_run`'s `finally`
	block guarantees an unlock for any exception raised inside the job's own
	Python code, but it cannot run if the worker process itself is killed
	outright (SIGKILL, OOM, a mid-scan `bench restart`) — this is the backstop
	for that case."""
	doctype = "Tea Lot Image Import"
	cutoff = add_to_date(now_datetime(), minutes=-STALE_SCAN_THRESHOLD_MINUTES)
	stale = frappe.get_all(
		doctype,
		filters={"scan_status": "Processing", "modified": ["<", cutoff]},
		pluck="name",
	)
	for doc_name in stale:
		frappe.db.set_value(doctype, doc_name, "scan_status", "Error", update_modified=True)
		files = frappe.qb.DocType(CHILD_DOCTYPE)
		frappe.qb.update(files).set(files.status, "Failed").set(
			files.error_msg, "Scan timed out or the worker crashed."
		).where((files.parent == doc_name) & (files.status == "Processing")).run()
		frappe.db.commit()
		frappe.publish_realtime(
			"tea_scan_progress",
			{
				"docname": doc_name,
				"processed": 0,
				"total": 0,
				"phase": "done",
				"status": "Error",
			},
			doctype=doctype,
			docname=doc_name,
		)


# ─────────────────────────────────────────────────────────────────────────
# CLAUDE CALL — one page, called in parallel from a ThreadPoolExecutor.
# Must stay a pure function (plain args in, dict out or raises): it runs
# inside worker threads and must never touch frappe.* internals.
# ─────────────────────────────────────────────────────────────────────────


def _call_claude_page(
	api_key: str, model: str, image: tuple[str, str], page_no: int, total_pages: int
) -> dict:
	import anthropic

	client = anthropic.Anthropic(api_key=api_key)
	image_b64, media_type = image
	content = [
		{"type": "text", "text": f"Page {page_no} of {total_pages}:"},
		{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
		{"type": "text", "text": _USER_PROMPT_PAGE, "cache_control": {"type": "ephemeral"}},
	]

	# Multi-image requests can exceed the SDK's 10-minute non-streaming limit, so this
	# goes through the streaming API even though only the final message is consumed.
	with client.messages.stream(
		model=model,
		max_tokens=16000,
		system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
		messages=[{"role": "user", "content": content}],
		output_config={"format": {"type": "json_schema", "schema": _PAGE_SCHEMA}, "effort": "medium"},
	) as stream:
		response = stream.get_final_message()

	if response.stop_reason == "refusal":
		raise ValueError(f"Claude declined to process page {page_no}.")
	text = next((block.text for block in response.content if block.type == "text"), None)
	if not text:
		raise ValueError(
			f"Claude returned no content for page {page_no} (stop_reason={response.stop_reason})."
		)
	return json.loads(text)


def _load_image_b64(file_url: str) -> tuple[str, str]:
	"""Return (base64 JPEG, media type) for the attached file, downscaled to
	`MAX_IMAGE_EDGE` on its long edge."""
	from PIL import Image

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	path = file_doc.get_full_path()

	buf = io.BytesIO()
	with Image.open(path) as img:
		img = img.convert("RGB")
		img.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
		img.save(buf, format="JPEG", quality=90)

	return base64.standard_b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"


# ─────────────────────────────────────────────────────────────────────────
# MERGE / TOTALS — pure functions, run in the main job thread after all
# page calls complete.
# ─────────────────────────────────────────────────────────────────────────


def _is_boundary_duplicate(prev_row: dict, row: dict) -> bool:
	"""True when `row` looks like the same lot as `prev_row`, split across a
	page break by the independent per-page calls."""
	if not row.get("lot_inv_no"):
		return False
	return (prev_row.get("lot_inv_no") or "").strip() == (row.get("lot_inv_no") or "").strip() and (
		prev_row.get("chest_nos") or ""
	).strip() == (row.get("chest_nos") or "").strip()


def _merge_pages(pages: list[dict]) -> dict:
	"""Combine per-page extractions (already in page order) into one: carry
	grade / company / garden / warehouse / ctc_no forward across blank cells,
	including across page boundaries, and dedupe a lot row split by a page
	break. Each page was scanned independently, so this rebuilds the
	cross-page reasoning the old single-request design left to the model."""
	items: list[dict] = []
	last = dict.fromkeys(_CARRY_FIELDS, "")
	header = {"broker": "", "auction_centre": "", "sale_no": 0, "acquisition_channel": ""}
	notes_parts: list[str] = []
	confidences: list[str] = []

	for page in pages:
		for field in header:
			if not header[field] and page.get(field):
				header[field] = page[field]
		if page.get("notes"):
			notes_parts.append(page["notes"])
		confidences.append((page.get("confidence") or "").lower())

		for row in page.get("items") or []:
			row = dict(row)
			for field in _CARRY_FIELDS:
				if row.get(field):
					last[field] = row[field]
				else:
					row[field] = last[field]
			if items and _is_boundary_duplicate(items[-1], row):
				continue
			items.append(row)

	order = ("low", "medium", "high")
	worst_confidence = (
		min(confidences, key=lambda c: order.index(c) if c in order else 2) if confidences else "high"
	)

	return {**header, "confidence": worst_confidence, "notes": " | ".join(notes_parts), "items": items}


def _compute_totals(items: list[dict]) -> tuple[int, float]:
	"""Sum straight from the already-extracted item rows — never trust the model
	to do cross-row or cross-page arithmetic; this is the whole point of
	computing totals in Python instead of asking for them in the schema."""
	total_packages = 0
	total_net = 0.0
	for row in items:
		match = re.match(r"\s*(\d+)", str(row.get("pkgs") or ""))
		if match:
			total_packages += int(match.group(1))
		total_net += flt(row.get("total_net"))
	return total_packages, flt(total_net)


def _parse_date(value: object) -> date | None:
	if not value or not isinstance(value, str):
		return None
	for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
		try:
			return datetime.strptime(value.strip(), fmt).date()
		except ValueError:
			continue
	return None
