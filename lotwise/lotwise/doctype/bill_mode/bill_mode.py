# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BillMode(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bill_mode: DF.Data
		days: DF.Int
		discount_percent: DF.Percent
		erpnext_payment_terms_template: DF.Link | None
		invoice_date: DF.Date | None
	# end: auto-generated types

	pass
