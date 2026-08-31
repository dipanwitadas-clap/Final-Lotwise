# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeaLotImageImport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from lotwise.lotwise.doctype.tea_lot_image_import_item.tea_lot_image_import_item import (
			TeaLotImageImportItem,
		)

		acquisition_channel: DF.Literal["", "Auction", "Private", "Outsourced"]
		broker: DF.Data | None
		items: DF.Table[TeaLotImageImportItem]
		sale_no: DF.Int
		scan_status: DF.Literal["Not Scanned", "Scanned", "Partial", "Error"]
		series: DF.Data | None
		source_image: DF.Attach | None
		total_net: DF.Float
		total_packages: DF.Int
	# end: auto-generated types

	pass
