# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import base64
import io
import json
from datetime import date, datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

DEFAULT_MODEL = "claude-sonnet-5"
MAX_IMAGE_EDGE = 1568

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

_EXTRACTION_SCHEMA = {
	"type": "object",
	"properties": {
		"broker": {"type": "string", "description": "Broker / auctioneer name, e.g. 'PARCON SILIGURI'"},
		"sale_no": {"type": "integer", "description": "Sale No; 0 if absent"},
		"acquisition_channel": {
			"type": "string",
			"enum": ["Auction", "Private", "Outsourced", ""],
			"description": "Infer from wording; '' if unclear",
		},
		"total_packages": {
			"type": "integer",
			"description": (
				"Sum of the PKGS totals from every page's 'Total :' line across all pages; 0 if absent"
			),
		},
		"total_net": {
			"type": "number",
			"description": (
				"Sum of the net totals from every page's 'Total :' line across all pages; 0 if absent"
			),
		},
		"confidence": {
			"type": "string",
			"enum": ["high", "medium", "low"],
			"description": "Overall confidence that every row was read correctly",
		},
		"notes": {"type": "string", "description": "Anything ambiguous or unreadable; '' if none"},
		"items": {"type": "array", "items": _ITEM_SCHEMA},
	},
	"required": [
		"broker",
		"sale_no",
		"acquisition_channel",
		"total_packages",
		"total_net",
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

_USER_PROMPT = """These images are consecutive pages (in order) of the same tea-auction broker's
printed lot catalogue, with handwritten marks added by hand. Treat them as one continuous
document and extract every page into a single combined `items` list.

Printed table columns (left to right): LOT INV NO, GRADE, CHEST NOS, GR. WT, NET WT, TOTAL NET,
PKGS, AWR DT, GP NO/DT, MFG MONTH/YEAR, LOCATION.

Structure:
- Bold centred lines above a block of rows give the COMPANY (e.g. "RYDAK SYNDICATE LIMITED"),
  then the GARDEN / estate (e.g. "BARADIGHI (DO)"). A code such as "NTCL(63)" or
  "KTTWPL - UNIT - 1(39)" is the WAREHOUSE. Apply the current company / garden / warehouse to
  every row until the heading changes, including carrying it across a page boundary if a block
  continues onto the next image without repeating its heading.
- When a GRADE cell is blank, carry down the last printed grade — including at the top of a
  later page, carried forward from the previous page if needed.
- Each printed lot line is one entry in `items`. If the last row of one page and the first row
  of the next page are the same lot split by the page break, include it only once.
- Each page's own "Total :" line near the bottom of a block gives that page's total packages and
  total net weight; report the sum across all pages in `total_packages` / `total_net`.

Handwritten marks:
- Red numbers next to a row = internal valuation.
- Blue text like "295 B", "300 B7", "OUT", "X" = bid price / status.
- Put every handwritten mark for a row into that row's `remarks` (e.g. "red 253; blue 295 B").
- Keep rows marked "OUT"; set their `remarks` to "OUT" (plus any other marks).

Header strip at the top of the first page: broker name (e.g. "PARCON SILIGURI"), series / CTC No
(e.g. "CTC 4"), and "Sale No : NN". Apply that series / CTC No to every row's `ctc_no` unless a
row explicitly prints a different one.

Extract every page now, combined into one result."""


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
		broker: DF.Data | None
		items: DF.Table[TeaLotImageImportItem]
		purchase_status: DF.Link | None
		sale_no: DF.Int
		scan_status: DF.Literal["Not Scanned", "Scanned", "Partial", "Error"]
		source_images: DF.Table[TeaLotImageImportSource]
		total_net: DF.Float
		total_packages: DF.Int
	# end: auto-generated types

	@frappe.whitelist()
	def scan_image(self) -> dict:
		"""Extract lot data from `source_images` with Claude and fill header + `items`."""
		if not self.source_images:
			frappe.throw(_("Attach at least one source image before scanning."))

		api_key = frappe.conf.get("anthropic_api_key")
		if not api_key:
			frappe.throw(
				_(
					"Anthropic API key is not configured. Add 'anthropic_api_key' to the site config "
					"(bench set-config anthropic_api_key ... / Frappe Cloud site Config)."
				)
			)

		try:
			images = [_load_image_b64(row.file_url) for row in self.source_images]
			data = _call_claude(api_key, images)
			self._apply_extraction(data)
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), "Tea Lot Image Import: scan failed")
			self.scan_status = "Error"
			self.save()
			frappe.msgprint(_("Image scan failed: {0}").format(str(exc)), indicator="red")
			return {"rows": len(self.items), "scan_status": self.scan_status, "error": str(exc)}

		self.save()
		return {"rows": len(self.items), "scan_status": self.scan_status}

	def _apply_extraction(self, data: dict) -> None:
		"""Map the extraction JSON onto the document. Header fields are only set when
		empty (so a user can pre-fill them); totals and `items` are always replaced."""
		if not self.broker and data.get("broker"):
			self.broker = data["broker"]
		if not self.sale_no and data.get("sale_no"):
			self.sale_no = cint(data["sale_no"])
		if not self.acquisition_channel and data.get("acquisition_channel") in _VALID_CHANNELS:
			self.acquisition_channel = data["acquisition_channel"]

		if data.get("total_packages"):
			self.total_packages = cint(data["total_packages"])
		if data.get("total_net"):
			self.total_net = flt(data["total_net"])

		rows = data.get("items") or []
		self.set("items", [])
		for row in rows:
			values = {field: (row.get(field) or "") for field in _TEXT_FIELDS}
			for field in _NUM_FIELDS:
				raw = row.get(field)
				values[field] = flt(raw) if raw not in (None, "") else 0
			values["awr_dt"] = _parse_date(row.get("awr_dt"))
			self.append("items", values)

		confidence = (data.get("confidence") or "").lower()
		if not rows:
			self.scan_status = "Error"
		elif confidence == "high":
			self.scan_status = "Scanned"
		else:
			self.scan_status = "Partial"


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


def _call_claude(api_key: str, images: list[tuple[str, str]]) -> dict:
	"""Send all page images (in page order) to Claude in one request and return the
	combined parsed extraction dict covering every page."""
	import anthropic

	client = anthropic.Anthropic(api_key=api_key)
	model = frappe.conf.get("anthropic_model") or DEFAULT_MODEL

	content: list[dict] = []
	for i, (image_b64, media_type) in enumerate(images, start=1):
		content.append({"type": "text", "text": f"Page {i} of {len(images)}:"})
		content.append(
			{
				"type": "image",
				"source": {
					"type": "base64",
					"media_type": media_type,
					"data": image_b64,
				},
			}
		)
	content.append({"type": "text", "text": _USER_PROMPT, "cache_control": {"type": "ephemeral"}})

	# Multi-image requests can exceed the SDK's 10-minute non-streaming limit, so this
	# must go through the streaming API even though we only consume the final message.
	with client.messages.stream(
		model=model,
		max_tokens=min(16000 * len(images), 64000),
		system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
		messages=[{"role": "user", "content": content}],
		output_config={
			"format": {"type": "json_schema", "schema": _EXTRACTION_SCHEMA},
			"effort": "medium",
		},
	) as stream:
		response = stream.get_final_message()

	if response.stop_reason == "refusal":
		raise ValueError("Claude declined to process this image.")

	text = next((block.text for block in response.content if block.type == "text"), None)
	if not text:
		raise ValueError(f"Claude returned no extraction content (stop_reason={response.stop_reason}).")

	return json.loads(text)


def _parse_date(value: object) -> date | None:
	if not value or not isinstance(value, str):
		return None
	for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
		try:
			return datetime.strptime(value.strip(), fmt).date()
		except ValueError:
			continue
	return None
