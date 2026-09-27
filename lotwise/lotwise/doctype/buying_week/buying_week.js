// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.ui.form.on("Buying Week", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Parse File"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before parsing."));
				return;
			}

			let method;
			if (
				frm.doc.acquisition_channel === "Auction" &&
				frm.doc.status === "Catalogue Loaded"
			) {
				method = "parse_auction_catalog";
			} else if (
				frm.doc.acquisition_channel === "Auction" &&
				frm.doc.status === "Deal Book Loaded"
			) {
				method = "parse_deal_book";
			} else {
				frappe.msgprint(
					__(
						"Set Acquisition Channel to Auction and Status to Catalogue Loaded or Deal Book Loaded before parsing."
					)
				);
				return;
			}

			frm.call({
				doc: frm.doc,
				method: method,
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

		if (
			frm.doc.acquisition_channel === "Auction" &&
			frm.doc.status === "Catalogue Loaded" &&
			(frm.doc.items || []).length > 0
		) {
			frm.add_custom_button(__("Create Tea Lot"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Please save the document before creating Tea Lots."));
					return;
				}
				frappe.confirm(__("Create Tea Lots for all rows in the table?"), () => {
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
