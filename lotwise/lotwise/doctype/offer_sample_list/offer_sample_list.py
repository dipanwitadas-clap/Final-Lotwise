# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OfferSampleList(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		broker_name: DF.Link
		date: DF.Date
		from_broker: DF.Check
		from_garden: DF.Check
		image: DF.AttachImage | None
		no_of_lots: DF.Int
		no_of_marks: DF.Int
		remarks: DF.SmallText | None
		weight: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Offer Sample List"

	def autoname(self):
		from frappe.model.naming import getseries
		from frappe.utils import getdate

		date_str = getdate(self.date).strftime("%m-%d") if self.date else ""
		broker_initials = ""
		if self.broker_name:
			broker_initials = self.broker_name[:2].upper()

		prefix = f"SampleList-{date_str}-{broker_initials}-"
		self.name = prefix + getseries(prefix, 3)
