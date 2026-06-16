// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

// frappe.listview_settings["Broker Warehouse name code"] = {
// 	onload(listview) {
// 		listview.page.add_inner_button("Upload Data", () => {
// 			frappe.new_doc("Data Import", {
// 				reference_doctype: "Broker Warehouse name code",
// 			});
// 		});
// 	},
// };
const DOCTYPE = "Broker Warehouse name code";
const IMPORT_METHOD =
	"lotwise.lotwise.doctype.broker_warehouse_name_code.broker_warehouse_name_code.import_broker_data";

frappe.listview_settings[DOCTYPE] = {
	onload(listview) {
		listview.page.add_inner_button(__("Upload Data"), () => {
			new frappe.ui.FileUploader({
				doctype: DOCTYPE,
				folder: "Home",
				allow_multiple: false,
				dialog_title: __("Upload Broker Warehouse Data"),
				restrictions: { allowed_file_types: [".xlsx"], max_number_of_files: 1 },
				on_success: (file) => import_broker_data(file?.file_url, listview),
			});
		});
	},
};

function import_broker_data(file_url, listview) {
	if (!file_url) return frappe.msgprint(__("File upload failed. Please try again."));

	frappe.call({
		method: IMPORT_METHOD,
		args: { file_url },
		freeze: true,
		freeze_message: __("Importing data..."),
		callback: ({ message }) => {
			const is_duplicate_import = message.inserted === 0 && message.skipped > 0;

			frappe.msgprint({
				title: is_duplicate_import ? __("Already Imported") : __("Import Successful"),
				message: is_duplicate_import
					? __("{0} records skipped because they already exist.", [message.skipped])
					: __("{0} records inserted, {1} skipped.", [
							message.inserted,
							message.skipped,
					  ]),
				indicator: "green",
			});
			listview.refresh();
		},
	});
}
