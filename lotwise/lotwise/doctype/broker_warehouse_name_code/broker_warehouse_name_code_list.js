// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.listview_settings["Broker Warehouse name code"] = {
	onload(listview) {
		listview.page.add_inner_button("Upload Data", () => {
			frappe.new_doc("Data Import", {
				reference_doctype: "Broker Warehouse name code",
			});
		});
	},
};
