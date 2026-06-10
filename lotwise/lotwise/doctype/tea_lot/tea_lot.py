# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeaLot(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		grade: DF.Link
		intended_segment: DF.Link | None
		invoice_number: DF.Data
		mark: DF.Link
		net_weight_total: DF.Float
		packages: DF.Int
		packing: DF.Link | None
		seller: DF.Link
		status: DF.Literal["", "Offered", "Evaluated"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot"
