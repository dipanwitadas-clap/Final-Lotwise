# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeaEvaluation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		briskness: DF.Float
		colour: DF.Float
		evaluation_date: DF.Date
		liquor_mark: DF.Literal["", "A+", "A", "B+", "B", "C+", "C"]
		notes: DF.SmallText | None
		quality_grade: DF.Literal[
			"", "A", "A++", "A+++", "B", "B+", "B++", "B-", "C", "C+", "D", "D+", "E", "E+"
		]
		stage: DF.Literal[
			"", "Pre-purchase", "Arrival", "Blend QC", "Storage", "Purchase Sample", "Bag Sample"
		]
		strength: DF.Float
		suggested_valuation: DF.Currency
		taste: DF.Float
		taster: DF.Link
		tea_lot: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Tea Evaluation"
