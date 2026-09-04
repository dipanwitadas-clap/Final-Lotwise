// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tea Lot Image Import", {
	refresh(frm) {
		frm.add_custom_button(__("Upload Source Images"), () => {
			new frappe.ui.FileUploader({
				allow_multiple: true,
				is_private: true,
				restrictions: {
					allowed_file_types: ["image/*"],
					max_file_size: 15 * 1024 * 1024,
				},
				on_success(file) {
					const already = (frm.doc.source_images || []).some(
						(row) => row.file_name === file.file_name
					);
					if (already) {
						frappe.show_alert({
							message: __("{0} is already added.", [file.file_name]),
							indicator: "orange",
						});
						return;
					}
					frm.add_child("source_images", {
						file_name: file.file_name,
						file_url: file.file_url,
					});
					frm.refresh_field("source_images");
					frm.dirty();
				},
			});
		});

		if (frm.is_new()) return;

		frm.add_custom_button(__("Scan Image"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before scanning."));
				return;
			}
			if (!(frm.doc.source_images && frm.doc.source_images.length)) {
				frappe.msgprint(__("Upload at least one source image first."));
				return;
			}
			frappe.confirm(
				__(
					"Extract lot data from the attached images? This will replace the current items."
				),
				() => {
					frm.call({
						doc: frm.doc,
						method: "scan_image",
						freeze: true,
						freeze_message: __("Reading images with Claude…"),
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
