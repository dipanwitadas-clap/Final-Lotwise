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
		broker: DF.Link | None
		centre: DF.Data | None
		certification: DF.Data | None
		chest_serial_range: DF.Data | None
		division: DF.Data | None
		gp_date: DF.Date | None
		gp_no: DF.Data | None
		grade: DF.Link
		gross_wtpkg: DF.Float
		intended_segment: DF.Link | None
		invoice_number: DF.Data
		lot_no: DF.Data | None
		manufacturer_ref: DF.Data | None
		mark: DF.Link
		mfg_monthyear: DF.Data | None
		net_weight_total: DF.Float
		net_wtpkg: DF.Float
		packages: DF.Int
		packing: DF.Link | None
		sale_no: DF.Data | None
		seller: DF.Link
		status: DF.Literal["", "Offered", "Evaluated"]
		warehouselocation: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Lot"
