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
		awr_date: DF.Date | None
		blend: DF.Literal["", "PREMIUM PACK"]
		broker: DF.Link | None
		centre: DF.Data | None
		certification: DF.Data | None
		chest_serial_range: DF.Data | None
		density: DF.Float
		division: DF.Data | None
		do_date: DF.Data | None
		do_reference: DF.Data | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		grade: DF.Link | None
		gross_wtpkg: DF.Float
		holding_status: DF.Literal["", "Committed", "Received", "In Stock"]
		intended_segment: DF.Link | None
		invoice_number: DF.Data
		liquor_mark: DF.Literal["", "A+", "A", "B+", "B", "C+", "C"]
		lot_no: DF.Data | None
		manufacturer_ref: DF.Data | None
		mark: DF.Link
		mfg_monthyear: DF.Data | None
		net_weight_total: DF.Float
		net_wtpkg: DF.Float
		packages: DF.Int
		packing: DF.Link | None
		purchase_date: DF.Date | None
		purchase_from: DF.Data | None
		purchase_invoice_date: DF.Date | None
		purchase_invoice_no: DF.Int
		rate: DF.Currency
		sale_no: DF.Data | None
		seller: DF.Link | None
		source_doctype: DF.Link | None
		source_doctype_id: DF.DynamicLink | None
		status: DF.Literal["", "Offered", "Evaluated"]
		total_amount_as_per_to_tax_invoice: DF.Float
		warehouse_name: DF.Data | None
		warehouselocation: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot"
