# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
import openpyxl
from frappe import _
from frappe.model.document import Document


class BrokerWarehousenamecode(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		short_name: DF.Data | None
		stac_code: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Broker Warehouse name code"


REQUIRED_HEADERS = {"SHORT NAME", "STAC CODE"}


def _val(value) -> str:
	return str(value or "").strip()


@frappe.whitelist(methods=["POST"])
def import_broker_data(file_url: str):
	"""Import Broker Warehouse data from XLSX. Inserts new, skips duplicates."""
	if not frappe.has_permission(BrokerWarehousenamecode._DOCTYPE_NAME, "create"):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	if not file_url:
		frappe.throw(_("Upload a file first."))

	wb = openpyxl.load_workbook(
		frappe.get_doc("File", {"file_url": file_url}).get_full_path(), data_only=True
	)
	try:
		rows = wb.active.iter_rows(values_only=True)
		headers = [_val(c).upper() for c in next(rows, [])]

		missing = REQUIRED_HEADERS - set(headers)
		if missing:
			frappe.throw(_("Missing columns: {0}").format(", ".join(sorted(missing))))

		# Collect unique records
		records = {}
		for row in rows:
			data = dict(zip(headers, row, strict=False))
			short_name = _val(data.get("SHORT NAME"))
			stac_code = _val(data.get("STAC CODE"))
			if short_name and short_name not in records:
				records[short_name] = stac_code

		# Check existing in DB
		existing = set()
		if records:
			existing = set(
				frappe.get_all(
					BrokerWarehousenamecode._DOCTYPE_NAME,
					filters={"short_name": ["in", list(records)]},
					pluck="short_name",
				)
			)

		# Insert new records
		inserted = skipped = 0
		for short_name, stac_code in records.items():
			if short_name in existing:
				skipped += 1
				continue
			frappe.get_doc(
				{
					"doctype": BrokerWarehousenamecode._DOCTYPE_NAME,
					"short_name": short_name,
					"stac_code": stac_code,
				}
			).insert()
			inserted += 1

		return {"success": True, "inserted": inserted, "skipped": skipped}
	finally:
		wb.close()
