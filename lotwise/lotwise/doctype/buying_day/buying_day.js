// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

const COMMON_START = ["Draft"];
const COMMON_END = ["Ordered", "Received", "Invoiced", "Paid", "Closed"];
const STATUS_OPTIONS = {
	Auction: [...COMMON_START, "Catalogue Loaded", "Deal Book Loaded", ...COMMON_END],
	PrivateInternal: [
		...COMMON_START,
		"Offer Sample Evaluation Load",
		"Purchase list Loaded",
		...COMMON_END,
	],
	PrivateExternal: [...COMMON_START, "Purchase list Loaded", ...COMMON_END],
};
const ALL_STATUS_OPTIONS = [
	...COMMON_START,
	"Catalogue Loaded",
	"Deal Book Loaded",
	"Offer Sample Evaluation Load",
	"Purchase list Loaded",
	...COMMON_END,
];

function catalogue_error_count(frm) {
	if (frm.doc.acquisition_channel !== "Auction") return 0;
	return (frm.doc.items || []).filter((r) => r.row_status === "Error").length;
}

function offer_sample_error_count(frm) {
	if (frm.doc.acquisition_channel !== "Private" || frm.doc.purchase_type !== "Internal")
		return 0;
	return (frm.doc.offer_sample_evaluation || []).filter(
		(r) => r.row_status === "Error" || r.eval_status === "Error"
	).length;
}

function offer_sample_all_done(frm) {
	const rows = frm.doc.offer_sample_evaluation || [];
	const ok = ["Created", "Duplicate"];
	return (
		rows.length > 0 &&
		rows.every((r) => ok.includes(r.row_status) && ok.includes(r.eval_status))
	);
}

function catalogue_all_done(frm) {
	const rows = frm.doc.items || [];
	return rows.length > 0 && rows.every((r) => ["Created", "Duplicate"].includes(r.row_status));
}

function set_status_options(frm) {
	let key = frm.doc.acquisition_channel;
	if (key === "Private") {
		key = frm.doc.purchase_type === "External" ? "PrivateExternal" : "PrivateInternal";
	}
	const options = STATUS_OPTIONS[key] || ALL_STATUS_OPTIONS;
	frm.set_df_property("status", "options", options.join("\n"));
	frm.refresh_field("status");
}

frappe.ui.form.on("Buying Day", {
	acquisition_channel(frm) {
		set_status_options(frm);
	},

	purchase_type(frm) {
		set_status_options(frm);
		if (
			frm.doc.purchase_type === "External" &&
			frm.doc.status === "Offer Sample Evaluation Load"
		) {
			frm.set_value("status", "Purchase list Loaded");
		}
	},

	status(frm) {
		if (frm.doc.status === "Deal Book Loaded" && catalogue_error_count(frm)) {
			frappe.msgprint(
				__(
					"Auction Catalogue Items has Error rows. Fix them before moving to Deal Book Loaded."
				)
			);
			frm.set_value("status", "Catalogue Loaded");
			return;
		}
		if (frm.doc.status === "Purchase list Loaded" && offer_sample_error_count(frm)) {
			frappe.msgprint(
				__(
					"Offer Sample Evaluation has Error rows. Fix them before moving to Purchase list Loaded."
				)
			);
			frm.set_value("status", "Offer Sample Evaluation Load");
			return;
		}
		const purchase_status_map = {
			Draft: "Offer",
			"Catalogue Loaded": "Offer",
			"Offer Sample Evaluation Load": "Offer",
			"Deal Book Loaded": "Purchase",
			"Purchase list Loaded": "Purchase",
		};
		const purchase_status = purchase_status_map[frm.doc.status];
		if (purchase_status) {
			frm.set_value("purchase_status", purchase_status);
		}
	},

	refresh(frm) {
		set_status_options(frm);
		if (frm.is_new()) return;

		const catalogue_errors = catalogue_error_count(frm);
		if (catalogue_errors) {
			frm.dashboard.set_headline_alert(
				__(
					"{0} Error row(s) in Auction Catalogue Items. Fix them and run Create Tea Lot again; Deal Book steps are locked.",
					[catalogue_errors]
				),
				"red"
			);
		}

		const offer_sample_errors = offer_sample_error_count(frm);
		if (offer_sample_errors) {
			frm.dashboard.set_headline_alert(
				__(
					"{0} Error row(s) in Offer Sample Evaluation. Fix them and run Create Tea Lot again; Purchase list Loaded is locked.",
					[offer_sample_errors]
				),
				"red"
			);
		}

		const has_errors = (table) =>
			(frm.doc[table] || []).some(
				(r) => r.row_status === "Error" || r.eval_status === "Error"
			);
		const po_pending = (table) =>
			!has_errors(table) &&
			(frm.doc[table] || []).some((r) => r.batch_no && !r.purchase_order);

		// Once Create PO is available it is the only action button on the form
		const po_method = {
			Auction: ["deal_book_items", "create_purchase_orders"],
			Private: ["private_purchase_list", "create_private_purchase_orders"],
		}[frm.doc.acquisition_channel];
		if (po_method && po_pending(po_method[0])) {
			const confirm_message =
				frm.doc.acquisition_channel === "Auction"
					? __("Create Purchase Orders (one per Broker) for rows with a Batch?")
					: __("Create Purchase Orders (one per Seller + Invoice / Bill Mode)?");
			frm.add_custom_button(__("Create PO"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Please save the document before creating records."));
					return;
				}
				frappe.confirm(confirm_message, () => {
					frm.call({
						doc: frm.doc,
						method: po_method[1],
						freeze: true,
						freeze_message: __("Creating Purchase Orders…"),
					}).then((r) => {
						frm.reload_doc();
						const m = r.message || {};
						frappe.msgprint(
							__("Created: {0}  ·  Errors: {1}", [m.created || 0, m.errors || 0])
						);
					});
				});
			}).addClass("btn-primary");
			return;
		}

		const deal_book_blocked = catalogue_errors && frm.doc.status !== "Catalogue Loaded";
		const os_done =
			frm.doc.acquisition_channel === "Private" &&
			frm.doc.status === "Offer Sample Evaluation Load" &&
			offer_sample_all_done(frm);
		const after_order = ["Ordered", "Received", "Invoiced", "Paid", "Closed"].includes(
			frm.doc.status
		);
		const cat_done =
			frm.doc.acquisition_channel === "Auction" &&
			frm.doc.status === "Catalogue Loaded" &&
			catalogue_all_done(frm);
		if (!os_done && !cat_done && !after_order)
			frm.add_custom_button(__("Read File"), () => {
				if (deal_book_blocked) {
					frappe.msgprint(__("Fix the Error rows in Auction Catalogue Items first."));
					return;
				}
				if (frm.is_dirty()) {
					frappe.msgprint(__("Please save the document before reading the file."));
					return;
				}

				let method;
				if (frm.doc.acquisition_channel === "Private") {
					if (frm.doc.status === "Offer Sample Evaluation Load") {
						if (!frm.doc.offer_sample_evaluation_file) {
							frappe.msgprint(
								__("Please attach the Offer Sample Evaluation File first.")
							);
							return;
						}
						method = "parse_offer_sample_evaluation";
					} else {
						if (!frm.doc.purchase_list_file) {
							frappe.msgprint(
								__("Please attach the Private Purchase List File first.")
							);
							return;
						}
						method = "parse_private_purchase_list";
					}
				} else if (
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
							"Set Acquisition Channel to Auction and Status to Catalogue Loaded or Deal Book Loaded before reading the file."
						)
					);
					return;
				}

				frm.call({
					doc: frm.doc,
					method: method,
					freeze: true,
					freeze_message: __("Reading file…"),
				}).then((r) => {
					frm.reload_doc();
					const rows = (r.message && r.message.rows) || 0;
					frappe.show_alert({
						message: __("Read {0} rows", [rows]),
						indicator: "blue",
					});
				});
			});

		const run_create = (method, confirm_message, freeze_message) => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before creating records."));
				return;
			}
			frappe.confirm(confirm_message, () => {
				frm.call({
					doc: frm.doc,
					method: method,
					freeze: true,
					freeze_message: freeze_message,
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
		};

		if (
			frm.doc.acquisition_channel === "Auction" &&
			frm.doc.status === "Catalogue Loaded" &&
			!cat_done &&
			(frm.doc.items || []).length > 0
		) {
			frm.add_custom_button(__("Create Tea Lot"), () =>
				run_create(
					"create_tea_lots",
					__("Create Tea Lots for all rows in the table?"),
					__("Creating Tea Lots…")
				)
			).addClass("btn-primary");
		}

		if (
			frm.doc.acquisition_channel === "Private" &&
			frm.doc.status === "Offer Sample Evaluation Load" &&
			!os_done &&
			(frm.doc.offer_sample_evaluation || []).length > 0
		) {
			frm.add_custom_button(__("Offer Sample Evaluation"), () =>
				run_create(
					"create_tea_lots_and_evaluations_from_offer_samples",
					__("Create Tea Lots and Tea Evaluations for all Offer Sample rows?"),
					__("Creating Tea Lots & Evaluations…")
				)
			).addClass("btn-primary");
		}

		if (
			frm.doc.acquisition_channel === "Auction" &&
			frm.doc.status === "Deal Book Loaded" &&
			!catalogue_errors &&
			(frm.doc.deal_book_items || []).length > 0
		) {
			frm.add_custom_button(__("Create Tea Purchase"), () =>
				run_create(
					"create_tea_purchases",
					__("Create Tea Purchases for all rows in the table?"),
					__("Creating Tea Purchases…")
				)
			).addClass("btn-primary");
		}

		if (
			frm.doc.acquisition_channel === "Private" &&
			frm.doc.status === "Purchase list Loaded" &&
			(frm.doc.private_purchase_list || []).length > 0
		) {
			const create_purchase = () =>
				run_create(
					"create_private_tea_purchases",
					__("Create Tea Purchases for all rows in the table?"),
					__("Creating Tea Purchases…")
				);

			if (frm.doc.purchase_type === "External") {
				const group = __("External Private Purchase");
				const lots_done =
					frm.doc.private_purchase_list.length > 0 &&
					frm.doc.private_purchase_list.every((r) =>
						["Created", "Duplicate"].includes(r.row_status)
					);
				if (!lots_done) {
					frm.add_custom_button(
						__("Create Tea Lot"),
						() =>
							run_create(
								"create_tea_lots_from_private_purchase_list",
								__("Create Tea Lots for all rows in the table?"),
								__("Creating Tea Lots…")
							),
						group
					);
				}
				if (lots_done) {
					frm.add_custom_button(__("Create Tea Purchase"), create_purchase, group);
				}
				frm.page.inner_toolbar
					.find(
						`.inner-group-button[data-label="${encodeURIComponent(group)}"] > button`
					)
					.removeClass("btn-default")
					.addClass("btn-primary");
			} else {
				frm.add_custom_button(__("Create Tea Purchase"), create_purchase).addClass(
					"btn-primary"
				);
			}
		}

		// Export Errors dropdown - one option per child table that has Error rows
		const export_options = [
			["items", __("Auction Catalogue Items Errors")],
			["deal_book_items", __("Deal Book Items Errors")],
			["offer_sample_evaluation", __("Offer Sample Errors")],
			["private_purchase_list", __("Private Purchase List Errors")],
		].filter(([table]) => has_errors(table));

		export_options.forEach(([table, label]) => {
			frm.add_custom_button(label, () => export_errors(frm, table), __("Export Errors"));
		});
		if (export_options.length) {
			frm.page.inner_toolbar
				.find(
					`.inner-group-button[data-label="${encodeURIComponent(
						__("Export Errors")
					)}"] > button`
				)
				.removeClass("btn-default")
				.addClass("btn-danger");
		}
	},
});

function export_errors(frm, table) {
	frm.call({
		doc: frm.doc,
		method: "export_error_rows",
		args: { table: table },
		freeze: true,
		freeze_message: __("Exporting error rows…"),
	}).then((r) => {
		if (r.message && r.message.content) {
			const binary = atob(r.message.content);
			const bytes = new Uint8Array(binary.length);
			for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
			const blob = new Blob([bytes.buffer], {
				type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			});
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = r.message.filename || frm.doc.name + "_errors.xlsx";
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);
			frappe.show_alert({
				message: __("Error rows exported successfully."),
				indicator: "green",
			});
		} else {
			frappe.msgprint(__("No error data to export."));
		}
	});
}
