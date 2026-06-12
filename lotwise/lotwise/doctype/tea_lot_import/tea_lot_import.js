// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Tea Lot Import", {
// 	refresh(frm) {

// 	},
// });
// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tea Lot Import", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Parse File"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before parsing."));
				return;
			}
			frm.call({
				doc: frm.doc,
				method: "parse_file",
				freeze: true,
				freeze_message: __("Parsing file…"),
			}).then((r) => {
				frm.reload_doc();
				const rows = (r.message && r.message.rows) || 0;
				frappe.show_alert({
					message: __("Parsed {0} rows", [rows]),
					indicator: "blue",
				});
			});
		});

		if ((frm.doc.rows_parsed || 0) > 0) {
			frm.add_custom_button(__("Create Tea Lots"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Please save the document before creating Tea Lots."));
					return;
				}
				frappe.confirm(__("Create Tea Lots for all pending rows?"), () => {
					frm.call({
						doc: frm.doc,
						method: "create_tea_lots",
						freeze: true,
						freeze_message: __("Creating Tea Lots…"),
					}).then((r) => {
						frm.reload_doc();
						const m = r.message || {};
						frappe.msgprint(
							__("Created: {0}  ·  Errors: {1}  ·  Duplicates: {2}", [
								m.created || 0,
								m.errors || 0,
								m.duplicates || 0,
							])
						);
					});
				});
			}).addClass("btn-primary");
		}
	},
});
