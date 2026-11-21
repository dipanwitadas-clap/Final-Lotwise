frappe.ui.form.on("Buying Week", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Add Buying Day"), () => {
			frappe.new_doc("Buying Day", { buying_week: frm.doc.name });
		});
	},

	acquisition_channel(frm) {
		if (!frm.is_new() || frm.doc.acquisition_channel !== "Private") return;
		const today = moment();
		if (!frm.doc.week_no) frm.set_value("week_no", today.isoWeek());
		if (!frm.doc.season) frm.set_value("season", today.isoWeekYear());
	},
});
