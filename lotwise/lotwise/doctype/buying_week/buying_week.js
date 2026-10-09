frappe.ui.form.on("Buying Week", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Add Buying Day"), () => {
			frappe.new_doc("Buying Day", { buying_week: frm.doc.name });
		});
	},
});
