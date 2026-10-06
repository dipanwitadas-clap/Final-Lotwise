# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class TeaPurchase(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		batch_error: DF.SmallText | None
		batch_no: DF.Link | None
		broker: DF.Link | None
		broker_code: DF.Data | None
		deal_no: DF.Data | None
		grade: DF.Link | None
		invoice_number: DF.Data | None
		item: DF.Link | None
		lot_no: DF.Data | None
		mark: DF.Link | None
		net_weight_total: DF.Float
		packages: DF.Int
		purchase_status: DF.Link | None
		rate: DF.Currency
		sale_no: DF.Int
		season: DF.Int
		source_doctype: DF.Link | None
		source_doctype_id: DF.DynamicLink | None
		tea_lot: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if self.is_new() and self.acquisition_channel != "Auction":
			self.validate_batch_inputs()

	def after_insert(self):
		if self.acquisition_channel == "Auction":
			self.try_create_batch()
		else:
			self.create_batch()

	def on_update(self):
		# Retry once the missing Auction data has been filled in
		if self.acquisition_channel == "Auction" and not self.batch_no and not self.flags.in_insert:
			self.try_create_batch()

	def try_create_batch(self):
		"""Auction: create the Batch only when every part of its ID is present;
		otherwise record why in `batch_error` and leave the Tea Purchase saved."""
		error = self.get_batch_blockers()
		if not error:
			try:
				self.create_batch()
			except Exception as e:
				error = str(e)[:140]
		self.db_set("batch_error", error or None)

	def get_batch_blockers(self):
		missing = [
			_(self.meta.get_label(fieldname))
			for fieldname in ("invoice_number", "grade", "mark", "season", "sale_no")
			if not self.get(fieldname)
		]
		if missing:
			return _("Missing: {0}").format(", ".join(missing))

		batch_id = self.get_batch_id()
		if frappe.db.exists("Batch", batch_id):
			return _("Batch {0} already exists.").format(batch_id)

	def get_batch_id(self):
		parts = [self.invoice_number, self.grade, self.mark, self.season, self.sale_no]
		return "-".join(str(p) for p in parts if p)

	def validate_batch_inputs(self):
		for fieldname in ("invoice_number", "grade", "mark"):
			if not self.get(fieldname):
				frappe.throw(
					_("{0} is required to create the Batch.").format(_(self.meta.get_label(fieldname)))
				)

		batch_id = self.get_batch_id()
		if frappe.db.exists("Batch", batch_id):
			frappe.throw(_("Batch {0} already exists.").format(frappe.bold(batch_id)))

	def create_batch(self):
		item_code = self.get_or_create_item(f"CTC-{self.grade}")
		batch_id = self.get_batch_id()

		frappe.get_doc({"doctype": "Batch", "batch_id": batch_id, "item": item_code}).insert(
			ignore_permissions=True
		)

		self.db_set({"item": item_code, "batch_no": batch_id})
		self.sync_deal_book_row(item_code, batch_id)

	def sync_deal_book_row(self, item_code, batch_id):
		if self.source_doctype != "Buying Week" or not self.source_doctype_id:
			return

		frappe.db.set_value(
			"Buying Week Deal Book Tea",
			{"parent": self.source_doctype_id, "tea_purchase": self.name},
			{"item_code": item_code, "batch_no": batch_id},
		)

	def get_or_create_item(self, item_code):
		if frappe.db.exists("Item", item_code):
			if not frappe.db.get_value("Item", item_code, "has_batch_no"):
				frappe.throw(
					_("Item {0} exists but is not batch enabled (Has Batch No).").format(
						frappe.bold(item_code)
					)
				)
			return item_code

		if not frappe.db.exists("Item Group", "Raw Tea - CTC"):
			frappe.get_doc(
				{
					"doctype": "Item Group",
					"item_group_name": "Raw Tea - CTC",
					"parent_item_group": _("All Item Groups"),
					"is_group": 0,
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists("UOM", "Nos"):
			frappe.throw(_("UOM 'Nos' does not exist. Please create it first."))

		item = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_code,
			"item_group": "Raw Tea - CTC",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"has_batch_no": 1,
		}
		if frappe.get_meta("Item").has_field("gst_hsn_code"):
			item["gst_hsn_code"] = "090240"

		return frappe.get_doc(item).insert(ignore_permissions=True).name

	def autoname(self):
		"""Same naming scheme as Tea Lot's Auction/Outsourced branch
		(tea_lot.py) - deliberately kept identical so a Tea Lot and the Tea
		Purchase for the same physical lot share the same name string (they
		are different doctypes, so this is not a naming collision)."""
		if self.acquisition_channel in ("Auction", "Outsourced"):
			if not self.auction_centre:
				frappe.throw(_("Auction Centre is required to generate the Tea Purchase name."))

			auction_centre_code = frappe.db.get_value(
				"Auction Centre", self.auction_centre, "auction_centre_code"
			)
			if not auction_centre_code:
				frappe.throw(_("Auction Centre Code not found."))

			if not self.season:
				frappe.throw(_("Season is required to generate the Tea Purchase name."))

			if not self.sale_no:
				frappe.throw(_("Sale No is required to generate the Tea Purchase name."))

			if not self.lot_no:
				frappe.throw(_("Lot No is required to generate the Tea Purchase name."))

			self.name = f"{auction_centre_code}-{self.season}-{self.sale_no}-{self.lot_no}"
		else:
			self.name = make_autoname("TPUR-.YYYY.-.#####")
