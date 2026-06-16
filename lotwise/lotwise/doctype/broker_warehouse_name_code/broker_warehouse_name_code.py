# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt

import frappe
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


DOCTYPE_NAME = "Broker Warehouse name code"
REQUIRED_HEADERS = {"SHORT NAME", "STAC CODE"}


def _clean_cell(value) -> str:
	return str(value or "").strip()


@frappe.whitelist(methods=["POST"])
def import_broker_data(file_url: str):
	try:
		if not frappe.has_permission(DOCTYPE_NAME, "create"):
			frappe.throw(
				_("Not permitted to import Broker Warehouse data."),
				frappe.PermissionError,
			)

		if not file_url:
			frappe.throw(_("Please upload a file before importing."))

		file_path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()
		if not file_path.lower().endswith(".xlsx"):
			frappe.throw(_("Only .xlsx files are supported."))

		import openpyxl

		workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
		try:
			rows = workbook.active.iter_rows(values_only=True)
			headers = [_clean_cell(cell).upper() for cell in next(rows, [])]
			missing = REQUIRED_HEADERS - set(headers)

			if missing:
				frappe.throw(_("Missing required column(s): {0}").format(", ".join(sorted(missing))))

			records, inserted, skipped = {}, 0, 0
			for row in rows:
				row_data = dict(zip(headers, row, strict=False))
				short_name = _clean_cell(row_data.get("SHORT NAME"))
				stac_code = _clean_cell(row_data.get("STAC CODE"))

				if not short_name or short_name in records:
					skipped += 1
					continue

				records[short_name] = stac_code

			existing = set()
			if records:
				existing = set(
					frappe.get_all(
						DOCTYPE_NAME,
						filters={"short_name": ["in", list(records)]},
						pluck="short_name",
					)
				)

			for short_name, stac_code in records.items():
				if short_name in existing:
					skipped += 1
					continue

				try:
					frappe.get_doc(
						{
							"doctype": DOCTYPE_NAME,
							"short_name": short_name,
							"stac_code": stac_code,
						}
					).insert()
					inserted += 1
				except frappe.DuplicateEntryError:
					skipped += 1

			return {"success": True, "inserted": inserted, "skipped": skipped}
		finally:
			workbook.close()

	except (frappe.ValidationError, frappe.PermissionError):
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Broker Import Error")
		raise
