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
		evaluation_stage: DF.Link | None
		invoice_number: DF.Data | None
		liquor_mark: DF.Link | None
		lot_no: DF.Data | None
		mark: DF.Link | None
		notes: DF.SmallText | None
		quality_grade: DF.Link | None
		remarks: DF.Data | None
		strength: DF.Int
		suggested_valuation: DF.Currency
		taste: DF.Int
		taster: DF.Link
		tea_lot: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Evaluation"

	def on_update(self):
		"""Update linked Tea Lot evaluation_status to 'Evaluated' when a Tea Evaluation is created or updated."""
		if self.tea_lot:
			frappe.db.set_value("Tea Lot", self.tea_lot, "evaluation_status", "Evaluated")
