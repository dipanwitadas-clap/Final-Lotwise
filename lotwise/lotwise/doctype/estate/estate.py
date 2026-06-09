# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Estate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		estate_name: DF.Data
		notes: DF.SmallText | None
		region: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Estate"
