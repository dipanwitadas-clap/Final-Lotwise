# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BagSample(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bag_serial_number: DF.Data | None
		no_of_bags: DF.Int
		sample_qty: DF.Float
	# end: auto-generated types

	_DOCTYPE_NAME = "Bag Sample"
