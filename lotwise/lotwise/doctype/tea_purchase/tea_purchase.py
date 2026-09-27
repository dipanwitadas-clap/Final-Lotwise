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
		deal_no: DF.Data | None
		grade: DF.Link | None
		invoice_number: DF.Data | None
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
