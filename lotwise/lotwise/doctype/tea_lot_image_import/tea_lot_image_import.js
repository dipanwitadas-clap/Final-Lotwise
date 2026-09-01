// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tea Lot Image Import", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Scan Image"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before scanning."));
				return;
			}
			if (!frm.doc.source_image) {
				frappe.msgprint(__("Attach a source image first."));
				return;
			}
			frappe.confirm(
				__("Extract lot data from the attached image? This replaces the current items."),
				() => {
					frm.call({
						doc: frm.doc,
						method: "scan_image",
						freeze: true,
						freeze_message: __("Reading image with Claude…"),
					}).then((r) => {
						frm.reload_doc();
						const m = r.message || {};
						frappe.show_alert({
							message: __("Extracted {0} rows · status {1}", [
								m.rows || 0,
								m.scan_status || "?",
							]),
							indicator: m.scan_status === "Error" ? "red" : "green",
						});
					});
				}
			);
		}).addClass("btn-primary");
	},
});
