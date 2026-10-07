# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BuyingWeekPurchaseOrder(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		broker: DF.Link | None
		deal_date: DF.Date | None
		message: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		purchase_order: DF.Link | None
		supplier: DF.Link | None
	# end: auto-generated types

	pass
