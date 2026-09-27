# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BuyingWeekTea(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auction_date: DF.Date | None
		auction_valuation: DF.Currency
		base_price: DF.Currency
		broker_code: DF.Data | None
		buyer_export_address_code: DF.Data | None
		buyer_interstate_address_code: DF.Data | None
		buyer_within_address_code: DF.Data | None
		category_id: DF.Data | None
		deal_no: DF.Data | None
		deal_time: DF.Data | None
		export: DF.Data | None
		grade_raw: DF.Data | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		gross_weight: DF.Float
		gross_wtpkg: DF.Float
		interstate: DF.Data | None
		invoice_number: DF.Data | None
		invoice_weight: DF.Float
		last_sold_price: DF.Currency
		lot_no: DF.Data | None
		lot_type: DF.Data | None
		mark_packaging_comments: DF.SmallText | None
		mark_raw: DF.Data | None
		message: DF.SmallText | None
		net_weight: DF.Float
		origin_code: DF.Data | None
		package_nos: DF.Data | None
		package_type: DF.Data | None
		packages: DF.Int
		period_of_manufacture: DF.Data | None
		preference: DF.Data | None
		price_per_kg: DF.Currency
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		sale_no: DF.Int
		sample_qty: DF.Float
		season: DF.Int
		session_time: DF.Data | None
		session_type: DF.Data | None
		short_excess_weight: DF.Float
		source_row_type: DF.Literal["", "Auction Catalog", "Deal Book"]
		sub_tea_type: DF.Data | None
		tea_lot: DF.Link | None
		tea_purchase: DF.Link | None
		tea_type: DF.Data | None
		total_net_weight: DF.Float
		warehouse_name: DF.Data | None
		within: DF.Data | None
	# end: auto-generated types
