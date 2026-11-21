# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeaLotImageImportItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		awr_dt: DF.Date | None
		chest_nos: DF.Data | None
		company: DF.Data | None
		ctc_no: DF.Data | None
		garden: DF.Data | None
		gp_no_dt: DF.Data | None
		gr_wt: DF.Float
		grade: DF.Data | None
		location: DF.Data | None
		lot_inv_no: DF.Data | None
		mfg_month_year: DF.Data | None
		net_wt: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pkgs: DF.Data | None
		purchase_date: DF.Date | None
		region: DF.Data | None
		remarks: DF.SmallText | None
		total_net: DF.Float
		warehouse: DF.Data | None
	# end: auto-generated types
