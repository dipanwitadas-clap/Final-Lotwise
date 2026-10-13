# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class TeaEvaluationImportItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		actual_valuation: DF.Currency
		auction_centre: DF.Link | None
		briskness: DF.Int
		colour: DF.Int
		density: DF.Float
		evaluation_date: DF.Date | None
		evaluation_stage: DF.Link | None
		evaluation_status: DF.Link | None
		grade: DF.Link | None
		invoice_number: DF.Data | None
		liquor_mark: DF.Link | None
		lot_liquor_mark: DF.Link | None
		lot_no: DF.Data | None
		mark: DF.Link | None
		message: DF.SmallText | None
		notes: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		purchase_date: DF.Date | None
		purchase_status: DF.Link | None
		quality_grade: DF.Link | None
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		sale_no: DF.Int
		strength: DF.Int
		suggested_valuation: DF.Currency
		taste: DF.Int
		taster: DF.Link | None
		tea_lot: DF.Link
	# end: auto-generated types

	pass
