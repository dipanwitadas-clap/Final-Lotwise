# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class BuyingWeek(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.buying_week_day.buying_week_day import BuyingWeekDay

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		auction_centre: DF.Link | None
		purchase_type: DF.Literal["", "Internal", "External"]
		buying_days: DF.Table[BuyingWeekDay]
		company: DF.Link | None
		sale_no: DF.Int
		season: DF.Int
	# end: auto-generated types

	def validate(self):
		if self.acquisition_channel != "Private":
			self.purchase_type = None

	def autoname(self):
		if self.acquisition_channel == "Auction":
			code = frappe.db.get_value("Auction Centre", self.auction_centre, "auction_centre_code")
			if not code:
				frappe.throw(_("Auction Centre Code not found."))
			self.name = f"BW-{code}-{self.season}-{self.sale_no}"
		else:
			self.name = make_autoname("BW-.YYYY.-.#####")
