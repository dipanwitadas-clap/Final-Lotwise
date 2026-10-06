# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Broker(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auction_centre: DF.Link
		auction_centre_code: DF.Data
		broker_name: DF.Data
		broker_short_name: DF.Data
		supplier: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Broker"
