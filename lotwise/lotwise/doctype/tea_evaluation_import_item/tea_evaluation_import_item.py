# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class TeaEvaluationImportItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		briskness: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
		colour: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
		evaluation_date: DF.Date | None
		invoice_number: DF.Data | None
		liquor_mark: DF.Literal["", "A+", "A", "B+", "B", "C+", "C"]
		mark: DF.Link | None
		message: DF.SmallText | None
		notes: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quality_grade: DF.Literal[
			"", "A", "A++", "A+++", "B", "B+", "B++", "B-", "C", "C+", "D", "D+", "E", "E+"
		]
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		stage: DF.Literal[
			"", "Pre-purchase", "Arrival", "Blend QC", "Storage", "Purchase Sample", "Bag Sample"
		]
		strength: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
		suggested_valuation: DF.Currency
		taste: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
		taster: DF.Link | None
		tea_lot: DF.Link
	# end: auto-generated types

	pass
