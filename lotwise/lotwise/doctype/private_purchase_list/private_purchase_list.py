# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PrivatePurchaseList(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		batch_no: DF.Link | None
		bill_mode: DF.Data | None
		bilty_lr_no: DF.Data | None
		broker: DF.Data | None
		brokerage: DF.Currency
		brokerage_percent: DF.Percent
		delivery: DF.Literal["Garden delivers", "We collect"]
		density: DF.Float
		for_blend: DF.Data | None
		grade_raw: DF.Data | None
		item_code: DF.Link | None
		kg_short_per_package: DF.Float
		list_date: DF.Date | None
		list_no: DF.Data | None
		lot_invoice_no: DF.Data | None
		mark_raw: DF.Data | None
		message: DF.SmallText | None
		net_kg: DF.Float
		net_kg_per_package: DF.Float
		overall_rating: DF.Data | None
		packages: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		purchase_order: DF.Link | None
		rate_per_kg: DF.Currency
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		seller: DF.Data | None
		seller_gstin: DF.Data | None
		short_packages: DF.Int
		tax_invoice_date: DF.Date | None
		tax_invoice_no: DF.Data | None
		tea_lot: DF.Link | None
		tea_purchase: DF.Link | None
		transporter: DF.Data | None
		value: DF.Currency
		warehouse: DF.Data | None
	# end: auto-generated types

	pass
