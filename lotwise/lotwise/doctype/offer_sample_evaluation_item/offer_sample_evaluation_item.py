# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class OfferSampleEvaluationItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		b: DF.Data | None
		broker_direct: DF.Data | None
		c: DF.Data | None
		date: DF.Date | None
		eval_message: DF.SmallText | None
		eval_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		evaluation: DF.Link | None
		garden: DF.Data | None
		grade: DF.Data | None
		invoice_no: DF.Data | None
		message: DF.SmallText | None
		overall_rating: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pckgs: DF.Data | None
		qty: DF.Data | None
		region: DF.Data | None
		remark: DF.Data | None
		row_status: DF.Literal["Pending", "Created", "Error", "Duplicate"]
		s: DF.Data | None
		sl_no: DF.Data | None
		t: DF.Data | None
		taster: DF.Data | None
		tea_lot: DF.Link | None
	# end: auto-generated types

	pass
