# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Broker(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acquisition_channel: DF.Literal["", "Auction", "Private"]
		auction_centre: DF.Link | None
		auction_centre_code: DF.Data | None
		broker_name: DF.Data
		broker_short_name: DF.Data
		supplier: DF.Link | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Broker"

	def autoname(self):
		if self.acquisition_channel == "Private":
			self.name = f"{self.broker_name}-PVT"
		else:
			self.name = f"{self.broker_name}-{self.auction_centre}"

	def validate(self):
		if self.acquisition_channel == "Private":
			self.auction_centre = None
			self.auction_centre_code = None
		elif self.acquisition_channel == "Auction":
			for fieldname in ("auction_centre", "auction_centre_code", "supplier"):
				if not self.get(fieldname):
					frappe.throw(
						_("{0} is mandatory for Auction brokers.").format(self.meta.get_label(fieldname))
					)
