# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OfferSample(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		broker_name: DF.Link | None
		date: DF.Date
		image: DF.AttachImage | None
		no_of_lot: DF.Int
		no_of_mark: DF.Int
		remarks: DF.SmallText | None
		weight: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Offer Sample"
