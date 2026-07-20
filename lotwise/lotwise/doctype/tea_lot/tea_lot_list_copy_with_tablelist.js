frappe.listview_settings["Tea Lot"] = {
	onload: function (listview) {
		// "Evaluation Import" button
		listview.page.add_inner_button(__("Evaluation Import"), function () {
			frappe.call({
				method: "lotwise.lotwise.doctype.tea_lot.tea_lot.download_evaluation_import_xlsx",
				callback: function (r) {
					if (!r.message || !r.message.content) {
						frappe.msgprint(__("No data available for download."));
						return;
					}
					var binaryStr = atob(r.message.content);
					var byteArray = new Uint8Array(binaryStr.length);
					for (var i = 0; i < binaryStr.length; i++) {
						byteArray[i] = binaryStr.charCodeAt(i);
					}
					var filename = r.message.filename || "tea_evaluation_import.xlsx";
					var blob = new Blob([byteArray], {
						type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					});
					if (navigator.msSaveBlob) {
						navigator.msSaveBlob(blob, filename);
					} else {
						var url = URL.createObjectURL(blob);
						var a = document.createElement("a");
						a.href = url;
						a.download = filename;
						document.body.appendChild(a);
						a.click();
						setTimeout(function () {
							document.body.removeChild(a);
							URL.revokeObjectURL(url);
						}, 100);
					}
				},
			});
		});

		// Store reference to listview for filter access
		window._tea_lot_listview = listview;

		// Replace the standard list view result area with custom inline-editable table
		replace_list_result_with_datatable(listview);

		// Hook into listview refresh to re-apply our custom table after filters change
		listview.orig_refresh = listview.refresh;
		listview.refresh = function (refresh_header) {
			var self = this;
			return listview.orig_refresh.call(self, refresh_header).then(function () {
				reapply_custom_table(self);
			});
		};
	},

	// Add custom "Delete Selected" action to Frappe's built-in Actions menu
	get_actions: function (docnames) {
		console.log(docnames);
		console.log("Count:", docnames.length);

		if (!docnames || !docnames.length) return [];
		return [
			{
				label: __("Delete Selected"),
				action: function () {
					frappe.confirm(
						__(
							"Are you sure you want to delete {0} Tea Lot(s)? This will also delete linked evaluations.",
							[docnames.length]
						),
						function () {
							frappe.call({
								method: "lotwise.lotwise.doctype.tea_lot.tea_lot.delete_tea_lots",
								args: { names: JSON.stringify(docnames) },
								freeze: true,
								freeze_message: __("Deleting..."),
								callback: function (r) {
									if (r.message) {
										frappe.show_alert({
											message: __("{0} Tea Lot(s) deleted successfully.", [
												r.message.deleted_count,
											]),
											indicator: "green",
										});
										if (window._tea_lot_listview) {
											window._tea_lot_listview.refresh();
										}
									}
								},
							});
						}
					);
				},
			},
		];
	},
};

// ============================================================
// GLOBALS
// ============================================================

var all_lots = [];
var dropdown_options = {};
var edited_rows = {};
var current_start = 0;
var current_page_length = 20;
var total_count = 0;

// ============================================================
// RE-APPLY CUSTOM TABLE (after listview refresh)
// ============================================================

function reapply_custom_table(listview) {
	var $result = $(listview.page.main).find(".frappe-list .result");
	if ($result.length) {
		$result.hide();
		// Remove all original Frappe checkboxes so they don't interfere
		$result.find(".list-row-checkbox").remove();
	}

	var $existing = $("#evaluation_datatable_container");
	if ($existing.length) {
		$existing.html(
			'<div class="text-center text-muted" style="padding:30px;">' +
				'<i class="fa fa-spinner fa-spin"></i> Loading...' +
				"</div>"
		);
		load_tea_lots_for_datatable();
		return;
	}

	var $wrapper = $(
		'<div class="tea-lot-evaluation-datatable">' +
			'<div class="datatable-toolbar" style="padding:5px 15px 0;display:flex;justify-content:flex-end;align-items:center;">' +
			'<div style="display:flex;gap:8px;">' +
			'<button class="btn btn-primary btn-sm" id="save_evaluations_btn">' +
			'<i class="fa fa-save"></i> Create Evaluation' +
			"</button>" +
			"</div>" +
			"</div>" +
			'<div id="evaluation_datatable_container" style="padding:5px 5px 5px;">' +
			'<div class="text-center text-muted" style="padding:30px;">' +
			'<i class="fa fa-spinner fa-spin"></i> Loading...' +
			"</div>" +
			"</div>" +
			'<div class="datatable-pagination" style="padding:10px 15px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #dee2e6;">' +
			'<div class="pagination-info" style="font-size:12px;color:#666;"></div>' +
			'<div class="btn-group pagination-nav">' +
			'<button class="btn btn-default btn-sm" id="prev_page_btn" disabled>' +
			'<i class="fa fa-chevron-left"></i>' +
			"</button>" +
			'<button class="btn btn-default btn-sm" id="next_page_btn">' +
			'<i class="fa fa-chevron-right"></i>' +
			"</button>" +
			"</div>" +
			"</div>" +
			"</div>"
	);

	$result.after($wrapper);
	load_tea_lots_for_datatable();

	// Bind pagination events after wrapper is created
	bind_pagination_events();
}

// ============================================================
// INITIAL REPLACEMENT
// ============================================================

function replace_list_result_with_datatable(listview) {
	var check_interval = setInterval(function () {
		var $result = $(listview.page.main).find(".frappe-list .result");
		if ($result.length && $result.find(".list-row").length) {
			clearInterval(check_interval);
			reapply_custom_table(listview);
		}
	}, 300);
}

// ============================================================
// GET CURRENT FILTERS FROM LISTVIEW
// ============================================================

function get_list_filters() {
	var filters = {};
	try {
		var lv = window._tea_lot_listview;
		if (lv && lv.filter_area) {
			var filter_data = lv.filter_area.get();
			filter_data.forEach(function (f) {
				if (!f) return;
				var fieldname, condition, value;
				if (f.length === 4) {
					fieldname = f[1];
					condition = f[2];
					value = f[3];
				} else if (f.length >= 3) {
					fieldname = f[0];
					condition = f[1];
					value = f[2];
				} else {
					return;
				}
				if (fieldname && fieldname !== "Tea Lot" && value && String(value).trim() !== "") {
					filters[fieldname] = value;
				}
			});
		}
	} catch (e) {
		console.log("Error reading filters:", e);
	}
	return filters;
}

// ============================================================
// LOAD DATA FROM SERVER
// ============================================================

function load_tea_lots_for_datatable(start, page_length) {
	if (typeof start === "undefined") start = current_start;
	if (typeof page_length === "undefined") page_length = current_page_length;

	current_start = start;
	current_page_length = page_length;

	var filters = get_list_filters();

	frappe.call({
		method: "lotwise.lotwise.doctype.tea_lot.tea_lot.get_tea_lots_for_evaluation",
		args: {
			filters: JSON.stringify(filters),
			start: start,
			page_length: page_length,
		},
		callback: function (r) {
			if (r.message) {
				all_lots = r.message.lots || [];
				total_count = r.message.total_count || 0;
				dropdown_options = {
					stage: r.message.stage_options || [],
					liquor_mark: r.message.liquor_mark_options || [],
					quality_grade: r.message.quality_grade_options || [],
				};
				render_datatable();
				update_pagination_ui();
			} else {
				$("#evaluation_datatable_container").html(
					'<div class="alert alert-info">No data available.</div>'
				);
			}
		},
	});
}

// ============================================================
// ADD HIDDEN FRA PPE CHECKBOXES IN .result AREA
// ============================================================

function ensure_hidden_checkboxes() {
	var lv = window._tea_lot_listview;
	if (!lv) return;
	var $result = $(lv.page.main).find(".frappe-list .result");
	if (!$result.length) return;

	// Remove old ones to avoid duplicates
	$result.find(".custom-hidden-cb").remove();

	// Add one hidden checkbox per lot using Frappe's standard list-row-checkbox class
	all_lots.forEach(function (lot) {
		var $cb = $(
			'<input type="checkbox" class="list-row-checkbox custom-hidden-cb" ' +
				'data-name="' +
				frappe.utils.escape_html(lot.name) +
				'" ' +
				'style="display:none;" />'
		);
		$result.append($cb);
	});
}

function sync_hidden_checkboxes() {
	var lv = window._tea_lot_listview;
	if (!lv) return;
	var $result = $(lv.page.main).find(".frappe-list .result");
	if (!$result.length) return;

	// Sync each hidden checkbox with our visible checkbox
	all_lots.forEach(function (lot) {
		var $visible = $('.lot-select-checkbox[data-row-key="' + lot.name + '"]');
		var $hidden = $result.find('.list-row-checkbox[data-name="' + lot.name + '"]');
		if ($visible.length && $hidden.length) {
			$hidden.prop("checked", $visible.prop("checked"));
		}
	});

	// Notify Frappe's listview to update Actions button state
	lv.$checks = $result.find(".list-row-checkbox:checked");
	lv.on_row_checked();
}

// ============================================================
// RENDER THE CUSTOM DATATABLE
// ============================================================

function render_datatable() {
	if (!all_lots.length) {
		$("#evaluation_datatable_container").html(
			'<div class="alert alert-info">No Tea Lots found.</div>'
		);
		return;
	}

	// Add hidden Frappe checkboxes (clears old ones first)
	ensure_hidden_checkboxes();

	var html = '<div class="table-responsive" style="overflow-x:auto;">';
	html +=
		'<table class="table table-bordered" id="eval_datatable" style="white-space:nowrap;font-size:12px;">';
	html += "<thead><tr>";
	html +=
		'<th style="width:36px;text-align:center;vertical-align:middle;">' +
		'<input type="checkbox" id="select_all_lots" title="Select All" style="cursor:pointer;" /></th>';

	var readonly_cols = [
		{ key: "idx", label: "#", width: 35 },
		{ key: "name", label: "ID", width: 140, clickable: true },
		{ key: "sale_no", label: "Sale No", width: 80 },
		{ key: "lot_no", label: "Lot No", width: 80 },
		{ key: "auction_centre", label: "Action Centre", width: 100 },
		{ key: "grade", label: "Grade", width: 80 },
		{ key: "invoice_number", label: "Invoice No", type: "text", width: 100 },
		{ key: "mark", label: "Mark", type: "link", options: "Mark", width: 80 },
	];

	var editable_cols = [
		{ key: "taster", label: "Taster", type: "link", options: "Taster", width: 100 },
		{ key: "stage", label: "Stage", type: "select", options_key: "stage", width: 110 },
		{
			key: "liquor_mark",
			label: "Liquor Mark",
			type: "select",
			options_key: "liquor_mark",
			width: 100,
		},
		{ key: "evaluation_date", label: "Eval Date", type: "date", width: 105 },
		{ key: "suggested_valuation", label: "Suggested Val", type: "currency", width: 100 },
		{ key: "colour", label: "Colour", type: "number", width: 60 },
		{ key: "strength", label: "Strength", type: "number", width: 70 },
		{ key: "taste", label: "Taste", type: "number", width: 60 },
		{ key: "briskness", label: "Briskness", type: "number", width: 70 },
		{
			key: "quality_grade",
			label: "Quality Grade",
			type: "select",
			options_key: "quality_grade",
			width: 105,
		},
		{ key: "remarks", label: "Remarks", type: "data", width: 150 },
	];

	var all_cols = readonly_cols.concat(editable_cols);
	all_cols.forEach(function (col) {
		html +=
			'<th style="min-width:' +
			col.width +
			'px;position:relative;">' +
			'<span style="font-weight:600;color:#4b5563;font-size:11px;">' +
			frappe.utils.escape_html(col.label) +
			"</span></th>";
	});

	html +=
		'<th style="min-width:60px;text-align:center;">' +
		'<span style="font-weight:600;color:#4b5563;font-size:11px;">Save</span></th>';

	html += "</tr></thead><tbody>";

	all_lots.forEach(function (lot, idx) {
		var row_key = lot.name;
		html += '<tr data-row-key="' + row_key + '" data-idx="' + idx + '">';
		html +=
			'<td style="text-align:center;vertical-align:middle;padding:2px 4px;">' +
			'<input type="checkbox" class="lot-select-checkbox" data-row-key="' +
			row_key +
			'" style="cursor:pointer;" /></td>';

		readonly_cols.forEach(function (col) {
			var val = col.key === "idx" ? idx + 1 : lot[col.key] || "";
			if (col.clickable) {
				html +=
					'<td style="padding:4px 6px;">' +
					'<a href="#" class="lot-id-link" data-lot-name="' +
					frappe.utils.escape_html(val) +
					'" ' +
					'style="color:#1f5eff;font-weight:600;text-decoration:none;">' +
					frappe.utils.escape_html(String(val)) +
					"</a></td>";
			} else {
				html +=
					'<td style="padding:4px 6px;">' +
					frappe.utils.escape_html(String(val)) +
					"</td>";
			}
		});

		editable_cols.forEach(function (col) {
			html += '<td style="padding:2px 4px;">';
			html += get_editable_cell_html(col, row_key, "");
			html += "</td>";
		});

		html +=
			'<td style="text-align:center;padding:2px 4px;">' +
			'<button class="btn btn-success btn-xs save-row-btn" data-row-key="' +
			row_key +
			'" disabled>' +
			'<i class="fa fa-check"></i></button></td>';

		html += "</tr>";
	});

	html += "</tbody></table></div>";

	$("#evaluation_datatable_container").html(html);

	bind_editable_events();
	bind_save_buttons();
	bind_top_save_button();
	bind_id_click();
	bind_checkbox_events();
}

// ============================================================
// BIND ID CLICK
// ============================================================

function bind_id_click() {
	$("#eval_datatable")
		.off("click", ".lot-id-link")
		.on("click", ".lot-id-link", function (e) {
			e.preventDefault();
			var lot_name = $(this).data("lot-name");
			if (lot_name) {
				frappe.set_route("Form", "Tea Lot", lot_name);
			}
		});
}

// ============================================================
// GENERATE EDITABLE CELL HTML
// ============================================================

function get_editable_cell_html(col, row_key, current_value) {
	var name_attr =
		'name="eval_' +
		col.key +
		'" data-row-key="' +
		row_key +
		'" data-col-key="' +
		col.key +
		'"';
	var val = current_value || "";

	switch (col.type) {
		case "select":
			var opts = dropdown_options[col.options_key] || [];
			var h =
				'<select class="form-control input-xs eval-cell" ' +
				name_attr +
				' style="height:24px;font-size:11px;padding:1px 4px;">';
			h += '<option value=""></option>';
			opts.forEach(function (opt) {
				h +=
					'<option value="' +
					frappe.utils.escape_html(opt) +
					'"' +
					(val === opt ? " selected" : "") +
					">" +
					frappe.utils.escape_html(opt) +
					"</option>";
			});
			h += "</select>";
			return h;

		case "link":
			return (
				'<div style="display:flex;gap:2px;">' +
				'<input type="text" class="form-control input-xs eval-cell eval-link" ' +
				name_attr +
				' data-link-doctype="' +
				col.options +
				'"' +
				' value="' +
				frappe.utils.escape_html(val) +
				'"' +
				' style="height:24px;font-size:11px;padding:1px 4px;flex:1;" placeholder="Search..." autocomplete="off" />' +
				'<button class="btn btn-default btn-xs eval-link-btn" ' +
				'data-field="' +
				col.key +
				'" data-row-key="' +
				row_key +
				'" ' +
				'style="padding:1px 5px;height:24px;" title="Select link">' +
				'<i class="fa fa-external-link" style="font-size:10px;"></i></button></div>'
			);

		case "date":
			// 		if (!val) {
			// 	var today = frappe.datetime.str_to_user(frappe.datetime.get_today());
			// 	val = today; // e.g. 13/07/2026
			// }

			return (
				'<div style="display:flex;gap:2px;">' +
				'<input type="text" class="form-control input-xs eval-cell eval-date" ' +
				name_attr +
				' value="' +
				frappe.utils.escape_html(val) +
				'"' +
				' placeholder="dd/mm/yyyy"' +
				' style="height:24px;font-size:11px;padding:1px 4px;flex:1;" autocomplete="off" />' +
				'<button class="btn btn-default btn-xs eval-date-btn" ' +
				'data-field="' +
				col.key +
				'" data-row-key="' +
				row_key +
				'" ' +
				'style="padding:1px 5px;height:24px;" title="Select date">' +
				'<i class="fa fa-calendar" style="font-size:10px;"></i></button></div>'
			);

		case "number":
			return (
				'<input type="number" class="form-control input-xs eval-cell" ' +
				name_attr +
				' value="' +
				frappe.utils.escape_html(val) +
				'"' +
				' min="0" max="100"' +
				' style="height:24px;font-size:11px;padding:1px 4px;" />'
			);

		case "currency":
			return (
				'<input type="number" class="form-control input-xs eval-cell" ' +
				name_attr +
				' value="' +
				frappe.utils.escape_html(val) +
				'"' +
				' step="0.01" min="0"' +
				' style="height:24px;font-size:11px;padding:1px 4px;" />'
			);

		default:
			return (
				'<input type="text" class="form-control input-xs eval-cell" ' +
				name_attr +
				' value="' +
				frappe.utils.escape_html(val) +
				'"' +
				' style="height:24px;font-size:11px;padding:1px 4px;" autocomplete="off" />'
			);
	}
}

// ============================================================
// BIND EDITABLE CELL EVENTS
// ============================================================

function bind_editable_events() {
	$("#eval_datatable").on("change input", ".eval-cell", function () {
		var $cell = $(this);
		var row_key = $cell.data("row-key");
		var col_key = $cell.data("col-key");

		if (!edited_rows[row_key]) {
			edited_rows[row_key] = {};
		}
		edited_rows[row_key][col_key] = $cell.val();

		var $save_btn = $('button.save-row-btn[data-row-key="' + row_key + '"]');
		$save_btn.prop("disabled", false);
		$save_btn.removeClass("btn-success").addClass("btn-warning");
	});

	// Link button click - open a dialog to select link value
	$("#eval_datatable")
		.off("click", ".eval-link-btn")
		.on("click", ".eval-link-btn", function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			var field = $btn.data("field");
			var $input = $(
				'input.eval-link[data-row-key="' + row_key + '"][data-col-key="' + field + '"]'
			);
			var doctype = $input.data("link-doctype");

			if (!doctype) return;

			var d = new frappe.ui.Dialog({
				title: __("Select {0}", [doctype]),
				fields: [
					{
						fieldname: "link_field",
						label: doctype,
						fieldtype: "Link",
						options: doctype,
					},
				],
				primary_action_label: __("Select"),
				primary_action: function () {
					var val = d.get_values().link_field;
					if (val) {
						$input.val(val).trigger("change");
					}
					d.hide();
				},
			});
			d.show();
		});

	// Helper to init/show datepicker on a date input (only on button click)
	function show_datepicker($input) {
		// If already initialized, just show it
		if ($input.data("dp")) {
			$input.data("dp").show();
			return;
		}

		// Initialize Frappe's built-in datepicker once, reuse it
		var dp = $input
			.datepicker({
				language: "en",
				dateFormat: "dd/mm/yyyy",
				autoClose: true,
				onSelect: function () {
					$input.trigger("change");
				},
			})
			.data("datepicker");

		$input.data("dp", dp);
		dp.show();
	}

	// Date button click - open datepicker directly on the input field
	// Sirf calendar icon button click karne se calendar khulega
	$("#eval_datatable")
		.off("click", ".eval-date-btn")
		.on("click", ".eval-date-btn", function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			var field = $btn.data("field");
			var $input = $(
				'input.eval-date[data-row-key="' + row_key + '"][data-col-key="' + field + '"]'
			);
			show_datepicker($input);
		});
}

// ============================================================
// BIND SAVE BUTTONS
// ============================================================

function bind_save_buttons() {
	$("#eval_datatable")
		.off("click", ".save-row-btn")
		.on("click", ".save-row-btn", function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			save_row_evaluation(row_key, $btn);
		});
}

function bind_top_save_button() {
	$("#save_evaluations_btn")
		.off("click")
		.on("click", function () {
			var $btn = $(this);
			var row_keys = Object.keys(edited_rows);
			if (!row_keys.length) {
				frappe.show_alert({
					message: __("No rows to save. Edit some fields first."),
					indicator: "orange",
				});
				return;
			}

			$btn.prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i> Saving...');

			var promises = [];
			var saved_count = 0;

			row_keys.forEach(function (row_key) {
				promises.push(
					new Promise(function (resolve) {
						save_single_evaluation(row_key, function (success) {
							if (success) saved_count++;
							resolve();
						});
					})
				);
			});

			Promise.all(promises).then(function () {
				$btn.prop("disabled", false).html('<i class="fa fa-save"></i> Save Evaluations');
				frappe.show_alert({
					message: saved_count + " evaluation(s) created successfully.",
					indicator: "green",
				});
				edited_rows = {};
				$(".save-row-btn")
					.prop("disabled", true)
					.removeClass("btn-warning")
					.addClass("btn-success");
			});
		});
}

// ============================================================
// BIND CHECKBOX EVENTS
// ============================================================

function bind_checkbox_events() {
	// Select all
	$("#eval_datatable")
		.off("change", "#select_all_lots")
		.on("change", "#select_all_lots", function () {
			var checked = $(this).prop("checked");
			$(".lot-select-checkbox").prop("checked", checked);
			sync_hidden_checkboxes();
		});

	// Individual checkboxes
	$("#eval_datatable")
		.off("change", ".lot-select-checkbox")
		.on("change", ".lot-select-checkbox", function () {
			var total = $(".lot-select-checkbox").length;
			var checked = $(".lot-select-checkbox:checked").length;
			$("#select_all_lots").prop("checked", total === checked);
			sync_hidden_checkboxes();
		});
}

// ============================================================
// SAVE LOGIC
// ============================================================

function save_row_evaluation(row_key, $btn) {
	$btn.prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i>');

	save_single_evaluation(row_key, function (success) {
		if (success) {
			$btn.html('<i class="fa fa-check"></i>');
			$btn.removeClass("btn-warning").addClass("btn-success");
			delete edited_rows[row_key];
			frappe.show_alert({
				message: __("Evaluation created for {0}", [row_key]),
				indicator: "green",
			});
		} else {
			$btn.prop("disabled", false).html('<i class="fa fa-check"></i>');
			$btn.addClass("btn-danger").removeClass("btn-warning btn-success");
		}
	});
}

function save_single_evaluation(row_key, callback) {
	var $row = $('tr[data-row-key="' + row_key + '"]');
	var row_data = { tea_lot: row_key };

	var editable_keys = [
		"taster",
		"stage",
		"liquor_mark",
		"evaluation_date",
		"suggested_valuation",
		"colour",
		"strength",
		"taste",
		"briskness",
		"quality_grade",
		"remarks",
	];

	editable_keys.forEach(function (key) {
		var $cell = $row.find('.eval-cell[data-col-key="' + key + '"]');
		if ($cell.length) {
			var val = $cell.val();
			if (key === "evaluation_date" && val) {
				var parts = val.split("/");
				if (parts.length === 3) {
					row_data[key] = parts[2] + "-" + parts[1] + "-" + parts[0];
				} else {
					row_data[key] = val;
				}
			} else {
				row_data[key] = val;
			}
		}
	});
	var lot = all_lots.find(function (d) {
		return d.name === row_key;
	});

	if (lot) {
		row_data.invoice_number = lot.invoice_number;
		row_data.mark = lot.mark;
	}

	if (!row_data.taster || !row_data.stage || !row_data.evaluation_date) {
		frappe.msgprint(
			__("Row {0}: Taster, Stage, and Evaluation Date are required.", [row_key])
		);
		callback(false);
		return;
	}

	frappe.call({
		method: "lotwise.lotwise.doctype.tea_lot.tea_lot.create_tea_evaluation",
		args: row_data,
		callback: function (r) {
			callback(!!r.message);
		},
		error: function () {
			callback(false);
		},
	});
}

// ============================================================
// PAGINATION FUNCTIONS
// ============================================================

function update_pagination_ui() {
	var $pagination_info = $(".pagination-info");
	var $prev_btn = $("#prev_page_btn");
	var $next_btn = $("#next_page_btn");
	var $paging_btns = $(".btn-paging");

	if (!$pagination_info.length || !$prev_btn.length || !$next_btn.length) return;

	var start = current_start;
	var page_length = current_page_length;
	var end = Math.min(start + page_length, total_count);

	// Update info text
	if (total_count > 0) {
		$pagination_info.html(
			"Showing " + (start + 1) + " to " + end + " of " + total_count + " entries"
		);
	} else {
		$pagination_info.html("No entries found");
	}

	// Update page size button states (highlight active one)
	$paging_btns.removeClass("btn-info").prop("disabled", false);
	$paging_btns
		.filter('[data-value="' + page_length + '"]')
		.addClass("btn-info")
		.prop("disabled", true);

	// Update navigation button states
	$prev_btn.prop("disabled", start === 0);
	$next_btn.prop("disabled", end >= total_count);
}

function bind_pagination_events() {
	// Page size buttons (20, 100, 500, 2500)
	$(".btn-paging")
		.off("click")
		.on("click", function () {
			var $this = $(this);
			var new_page_length = parseInt($this.data("value"));

			// Update active state
			$(".btn-paging").removeClass("btn-info").prop("disabled", false);
			$this.addClass("btn-info").prop("disabled", true);

			// Reset to first page with new page size
			current_page_length = new_page_length;
			current_start = 0;
			load_tea_lots_for_datatable(0, new_page_length);
		});

	// Previous button
	$("#prev_page_btn")
		.off("click")
		.on("click", function () {
			if (current_start > 0) {
				var new_start = Math.max(0, current_start - current_page_length);
				load_tea_lots_for_datatable(new_start, current_page_length);
			}
		});

	// Next button
	$("#next_page_btn")
		.off("click")
		.on("click", function () {
			if (current_start + current_page_length < total_count) {
				var new_start = current_start + current_page_length;
				load_tea_lots_for_datatable(new_start, current_page_length);
			}
		});
}

// ============================================================
// STYLES
// ============================================================

$("<style>")
	.text(
		`
		.tea-lot-evaluation-datatable .table th {
			background: #f5f5f5;
			padding: 6px 4px;
			vertical-align: top;
			border-bottom: 2px solid #dee2e6;
		}
		.tea-lot-evaluation-datatable .table td {
			padding: 2px 4px;
			vertical-align: middle;
		}
		.tea-lot-evaluation-datatable .table tbody tr:hover {
			background: #f8faff;
		}
		.tea-lot-evaluation-datatable .eval-cell:focus {
			border-color: #1f5eff;
			box-shadow: 0 0 0 2px rgba(31,94,255,.12);
			outline: none;
		}
		.tea-lot-evaluation-datatable .save-row-btn {
			padding: 2px 8px;
			font-size: 11px;
		}
		.tea-lot-evaluation-datatable .table-responsive {
			max-height: calc(100vh - 300px);
			overflow-y: auto;
		}
		.tea-lot-evaluation-datatable #eval_datatable thead th {
			position: sticky;
			top: 0;
			background: #f5f5f5;
		}
	`
	)
	.appendTo("head");
