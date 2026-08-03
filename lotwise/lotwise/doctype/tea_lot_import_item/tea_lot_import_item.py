# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeaLotImportItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auction_centre: DF.Link | None
		bill_mode: DF.Data | None
		blend: DF.Data | None
		created_masters: DF.Data | None
		density: DF.Float
		grade_raw: DF.Data | None
		gross_wtpkg: DF.Float
		invoice_number: DF.Data | None
		liquor_mark: DF.Data | None
		lot_no: DF.Data | None
		mark_raw: DF.Data | None
		message: DF.SmallText | None
		net_weight_total: DF.Float
		packages: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		purchase_date: DF.Date | None
		purchase_from: DF.Data | None
		purchase_invoice_date: DF.Date | None
		purchase_invoice_no: DF.Data | None
		rate: DF.Currency
		remarks: DF.SmallText | None
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		sam_pkg: DF.Data | None
		sam_wt: DF.Data | None
		tea_lot: DF.Link | None
		total_amount_as_per_to_tax_invoice: DF.Float
		warehouse_name: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot Import Item"
