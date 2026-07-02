// // Copyright (c) 2026, BusinessThat.Works and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Tea Evaluation Import', {
// 	refresh: function(frm) {
// 		frm.disable_save();
// 	},

// 	parse_file: function(frm) {
// 		frm.call('parse_file').then(r => {
// 			frm.reload_doc();
// 			console.log(r);
// 			frappe.msgprint(__('Parsed {0} rows', [r.rows]));
// 		});
// 	},

// 	create_evaluations: function(frm) {
// 		frm.call('create_evaluations').then(r => {
// 			frm.reload_doc();
// 			frappe.msgprint(__('Created: {0}, Errors: {1}, Duplicates: {2}', [
// 				r.created, r.errors, r.duplicates
// 			]));
// 		});
// 	}
// });
// Copyright (c) 2026, BusinessThat.Works
// For license information, please see license.txt

frappe.ui.form.on("Tea Evaluation Import", {
	refresh(frm) {
		// frm.disable_save();

		// ==================================================
		// LOAD EXCEL DATA BUTTON
		// ==================================================

		if (frm.doc.import_file) {
			frm.add_custom_button(__("Load Excel Data"), function () {
				frm.call("load_excel_data").then((r) => {
					frappe.msgprint(__("Loaded {0} rows", [r.message.rows]));

					frm.reload_doc();
				});
			});
		}

		// ==================================================
		// CREATE TEA EVALUATION BUTTON
		// ==================================================

		if (frm.doc.items && frm.doc.items.length) {
			frm.add_custom_button(__("Create Evaluations"), function () {
				frappe.confirm(
					__("Are you sure you want to create Tea Evaluations?"),

					function () {
						frm.call("create_evaluations").then((r) => {
							frappe.msgprint(
								__("Created: {0}, Errors: {1}, Duplicate: {2}", [
									r.message.created,

									r.message.errors,

									r.message.duplicates,
								])
							);

							frm.reload_doc();
						});
					}
				);
			});
		}
	},
});
