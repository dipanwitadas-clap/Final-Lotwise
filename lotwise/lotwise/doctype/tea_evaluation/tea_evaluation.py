# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TeaEvaluation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		briskness: DF.Int
		colour: DF.Int
		density: DF.Float
		evaluation_date: DF.Date
		invoice_number: DF.Data | None
		liquor_mark: DF.Literal["", "A", "A-", "A+", "A++", "B", "B+", "B++", "B-", "C", "C-", "D"]
		lot_no: DF.Data | None
		mark: DF.Link | None
		notes: DF.SmallText | None
		quality_grade: DF.Literal[
			"", "A", "A++", "A+++", "B", "B+", "B++", "B-", "C", "C+", "D", "D+", "E", "E+"
		]
		remarks: DF.Data | None
		stage: DF.Literal[
			"", "Pre-purchase", "Arrival", "Blend QC", "Storage", "Purchase Sample", "Bag Sample"
		]
		strength: DF.Int
		suggested_valuation: DF.Currency
		taste: DF.Int
		taster: DF.Link
		tea_lot: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Evaluation"

	def on_update(self):
		"""Update linked Tea Lot status to 'Evaluated' when a Tea Evaluation is created or updated."""
		if self.tea_lot:
			frappe.db.set_value("Tea Lot", self.tea_lot, "status", "Evaluated")
