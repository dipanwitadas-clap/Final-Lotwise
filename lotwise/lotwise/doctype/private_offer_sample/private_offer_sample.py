# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PrivateOfferSample(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		broker: DF.Link | None
		date: DF.Date
		grade: DF.Link | None
		invoice_number: DF.Data | None
		mark: DF.Link | None
		nett_wt_kgs: DF.Float
		no_of_pkgs: DF.Int
		party_name: DF.Data | None
		sample_qty: DF.Float
		total_kgs: DF.Float
		wt_kgs: DF.Float
	# end: auto-generated types

	_DOCTYPE_NAME = "Private Offer Sample"
