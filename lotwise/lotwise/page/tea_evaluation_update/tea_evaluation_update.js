// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.pages["tea-evaluation-update"].on_page_load = function (wrapper) {
	new TeaEvaluationUpdatePage(wrapper);
};

// =============================================================================
// ICONS & SPINNER (module-level constants)
// =============================================================================

const TEA_EVAL_ICONS = {
	filter: '<path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>',
	clear: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
	taster: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>',
	edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/>',
	calendar:
		'<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
	valuation:
		'<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>',
	colour: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
	strength: '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>',
	taste: '<path d="M12 20a8 8 0 100-16 8 8 0 000 16z"/><path d="M12 14a2 2 0 100-4 2 2 0 000 4z"/>',
	briskness: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
	quality:
		'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
	density:
		'<rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="9" y1="10" x2="15" y2="10"/><line x1="9" y1="14" x2="15" y2="14"/>',
	save: '<polyline points="20 6 9 17 4 12"/>',
	save_all:
		'<path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
	export: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
	loading:
		'<circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>',
	prev: '<polyline points="15 18 9 12 15 6"/>',
	next: '<polyline points="9 18 15 12 9 6"/>',
};

function get_icon(name, size) {
	size = size || "14px";
	return (
		'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:' +
		size +
		";height:" +
		size +
		';vertical-align:middle;">' +
		(TEA_EVAL_ICONS[name] || "") +
		"</svg>"
	);
}

function get_spinner(size) {
	size = size || "14px";
	return (
		'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:' +
		size +
		";height:" +
		size +
		';animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>'
	);
}

// =============================================================================
// Tea Evaluation Update Page
// =============================================================================

function TeaEvaluationUpdatePage(wrapper) {
	this.wrapper = wrapper;
	this.page = null;

	// --- State ---
	this.all_evaluations = [];
	this.dropdown_options = { stage: [], liquor_mark: [], quality_grade: [] };
	this.edited_rows = {};
	this.current_start = 0;
	this.current_page_length = 20;
	this.total_count = 0;
	this.filter_values = {};
	this.filter_fields = {};

	// --- DOM Cache ---
	this.$table_container = null;
	this.$save_all_btn = null;
	this.$save_all_count = null;
	this.$prev_page_btn = null;
	this.$next_page_btn = null;
	this.$pagination_info = null;

	// --- Constants ---
	this.API_BASE = "lotwise.lotwise.page.tea_evaluation_update.tea_evaluation_update";

	// --- Column Definitions ---
	this.readonly_cols = [
		{ key: "idx", label: "#", width: 35 },
		{ key: "name", label: "ID", width: 140, clickable: true },
		{ key: "tea_lot", label: "Tea Lot", width: 140, clickable: true },
		{ key: "invoice_number", label: "Invoice No", width: 100 },
		{ key: "mark", label: "Mark", width: 80 },
		{ key: "lot_no", label: "Lot No", width: 100 },
		{ key: "stage", label: "Stage", width: 110 },
	];

	this.editable_cols = [
		{ key: "taster", label: "Taster", type: "link", options: "Taster", width: 100 },
		{
			key: "liquor_mark",
			label: "Liquor Mark",
			type: "select",
			options_key: "liquor_mark",
			width: 100,
		},
		{ key: "evaluation_date", label: "Eval Date", type: "date", width: 120 },
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
		{ key: "density", label: "Density", type: "float", width: 70 },
		{ key: "remarks", label: "Remarks", type: "data", width: 150 },
	];

	this.editable_keys = [
		"taster",
		"liquor_mark",
		"evaluation_date",
		"suggested_valuation",
		"colour",
		"strength",
		"taste",
		"briskness",
		"quality_grade",
		"density",
		"remarks",
	];

	this.init();
}

// =============================================================================
// PROTOTYPE METHODS
// =============================================================================

TeaEvaluationUpdatePage.prototype = {
	constructor: TeaEvaluationUpdatePage,

	// -------------------------------------------------------------------------
	// HELPER FUNCTIONS
	// -------------------------------------------------------------------------

	get_stage_badge_html: function (stage) {
		if (!stage) return "";
		var s = String(stage).toLowerCase().trim();
		var css_class = "";
		var label = stage;

		if (s === "draft" || s === "in stock" || s === "available") {
			css_class = "stage-draft";
		} else if (s === "pending" || s === "under evaluation") {
			css_class = "stage-pending";
		} else if (s === "approved" || s === "sold" || s === "completed") {
			css_class = "stage-approved";
		} else if (s === "rejected" || s === "cancelled" || s === "void") {
			css_class = "stage-rejected";
		} else {
			css_class = "stage-draft";
		}

		return (
			'<span class="stage-badge ' +
			css_class +
			'">' +
			frappe.utils.escape_html(label) +
			"</span>"
		);
	},

	// -------------------------------------------------------------------------
	// INITIALISATION
	// -------------------------------------------------------------------------

	init: function () {
		this.page = frappe.ui.make_app_page({
			parent: this.wrapper,
			title: __("Tea Evaluation Update"),
			single_column: true,
		});

		this.build_page();
		this.create_filter_fields();
		this.bind_events();
		this.load_data();

		this.page.add_inner_button(__("New Tea Evaluation"), () => {
			frappe.new_doc("Tea Evaluation");
		});
	},

	// -------------------------------------------------------------------------
	// BUILD PAGE
	// -------------------------------------------------------------------------

	build_page: function () {
		$(this.page.main).html(`
			<div class="tea-eval-page">
				<!-- FILTERS CARD -->
				<div class="card mb-2 shadow-sm rounded">
					<div class="card-header py-2 bg-white">
						<span class="d-flex align-items-center gap-1">
							${get_icon("filter", "16px")} Filters
						</span>
					</div>
					<div class="card-body py-2">
						<div class="row g-2 align-items-end eval-filter-grid">
							<div class="col eval-field">
								<label class="eval-field-label">Tea Lot</label>
								<div id="filter_tea_lot_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Invoice No</label>
								<div id="filter_invoice_number_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Lot No</label>
								<div id="filter_lot_no_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Mark</label>
								<div id="filter_mark_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Taster</label>
								<div id="filter_taster_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Stage</label>
								<div id="filter_stage_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Quality Grade</label>
								<div id="filter_quality_grade_field"></div>
							</div>
							<div class="col eval-field">
								<label class="eval-field-label">Eval Date</label>
								<div id="filter_evaluation_date_field"></div>
							</div>
							<div class="col-auto align-self-end eval-field-btn">
								<button class="btn btn-outline-secondary btn-sm" id="clear_filters_btn">
									${get_icon("clear", "14px")} Clear
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- TOOLBAR -->
				<div class="mb-2">
				<div class="d-flex flex-wrap gap-1 align-items-center">
				<button class="btn btn-outline-primary btn-sm" id="bulk_update_taster_btn">
					${get_icon("taster", "14px")} Taster
				</button>
				<button class="btn btn-outline-primary btn-sm" data-field="evaluation_date">
							${get_icon("calendar", "14px")} Eval Date
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="liquor_mark">
							${get_icon("edit", "14px")} Liquor Mark
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="suggested_valuation">
							${get_icon("valuation", "14px")} Suggested Val
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="colour">
							${get_icon("colour", "14px")} Colour
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="strength">
							${get_icon("strength", "14px")} Strength
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="taste">
							${get_icon("taste", "14px")} Taste
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="briskness">
							${get_icon("briskness", "14px")} Briskness
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="quality_grade">
							${get_icon("quality", "14px")} Quality Grade
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="density">
							${get_icon("density", "14px")} Density
						</button>
						<button class="btn btn-success btn-sm fw-semibold" id="save_all_btn">
							${get_icon("save_all", "16px")} Save All
							<span class="badge bg-light text-dark ms-1" id="save_all_count" style="display:none;">0</span>
						</button>
						<button class="btn btn-outline-success btn-sm fw-semibold" id="export_excel_btn">
							${get_icon("export", "14px")} Export Excel
						</button>
					</div>
				</div>

				<!-- TABLE CARD -->
				<div class="card mb-2 shadow-sm rounded">
					<div class="card-body p-0">
						<div id="eval_table_container" class="eval-loading">
							${get_spinner("32px")}
							<div>Loading Tea Evaluations...</div>
						</div>
					</div>
					<div class="card-footer py-2 bg-white">
						<div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
							<span class="text-muted small" id="pagination_info">No entries found</span>
							<div class="d-flex align-items-center gap-2">
								<div class="btn-group" role="group">
									<button class="btn btn-outline-secondary btn-sm eval-page-size" data-value="20">20</button>
									<button class="btn btn-outline-secondary btn-sm eval-page-size" data-value="100">100</button>
									<button class="btn btn-outline-secondary btn-sm eval-page-size" data-value="500">500</button>
									<button class="btn btn-outline-secondary btn-sm eval-page-size" data-value="2500">2500</button>
								</div>
								<div class="btn-group" role="group">
									<button class="btn btn-outline-primary btn-sm" id="prev_page_btn" disabled>
										${get_icon("prev", "14px")}
									</button>
									<button class="btn btn-outline-primary btn-sm" id="next_page_btn">
										${get_icon("next", "14px")}
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		// Cache DOM elements
		this.$table_container = $("#eval_table_container");
		this.$save_all_btn = $("#save_all_btn");
		this.$save_all_count = $("#save_all_count");
		this.$prev_page_btn = $("#prev_page_btn");
		this.$next_page_btn = $("#next_page_btn");
		this.$pagination_info = $("#pagination_info");

		// Set initial active page size
		this.$save_all_count.hide();
		$(".eval-page-size[data-value='20']").addClass("active");
	},

	// -------------------------------------------------------------------------
	// FILTER FIELDS (Frappe Native Controls)
	// -------------------------------------------------------------------------

	create_filter_fields: function () {
		var me = this;
		var filter_configs = [
			{ fieldname: "tea_lot", label: "Tea Lot", fieldtype: "Link", options: "Tea Lot" },
			{ fieldname: "invoice_number", label: "Invoice No", fieldtype: "Data" },
			{ fieldname: "lot_no", label: "Lot No", fieldtype: "Data" },
			{ fieldname: "mark", label: "Mark", fieldtype: "Link", options: "Mark" },
			{ fieldname: "taster", label: "Taster", fieldtype: "Link", options: "Taster" },
			{ fieldname: "stage", label: "Stage", fieldtype: "Select", options: "" },
			{
				fieldname: "quality_grade",
				label: "Quality Grade",
				fieldtype: "Select",
				options: "",
			},
			{ fieldname: "evaluation_date", label: "Eval Date", fieldtype: "Date" },
		];

		filter_configs.forEach(function (cfg) {
			var df = {
				fieldname: cfg.fieldname,
				label: cfg.label,
				fieldtype: cfg.fieldtype,
				options: cfg.options,
				change: function () {
					me.collect_filters();
					me.current_start = 0;
					me.load_data();
				},
			};
			var field = frappe.ui.form.make_control({
				parent: $("#filter_" + cfg.fieldname + "_field"),
				df: df,
				render_input: true,
			});
			field.refresh();
			me.filter_fields[cfg.fieldname] = field;
		});
	},

	update_filter_select_options: function () {
		var stage_field = this.filter_fields.stage;
		if (stage_field) {
			stage_field.df.options = ["", ...this.dropdown_options.stage].join("\n");
			stage_field.refresh();
		}

		var quality_field = this.filter_fields.quality_grade;
		if (quality_field) {
			quality_field.df.options = ["", ...this.dropdown_options.quality_grade].join("\n");
			quality_field.refresh();
		}
	},

	// update_filter_select_options: function () {
	// 	var stage_field = this.filter_fields["stage"];
	// 	if (stage_field) {
	// 		stage_field.set_options([""].concat(this.dropdown_options.stage).join("\n"));
	// 		stage_field.refresh();
	// 	}
	// 	var qg_field = this.filter_fields["quality_grade"];
	// 	if (qg_field) {
	// 		qg_field.set_options([""].concat(this.dropdown_options.quality_grade).join("\n"));
	// 		qg_field.refresh();
	// 	}
	// },

	// -------------------------------------------------------------------------
	// EVENT BINDING
	// -------------------------------------------------------------------------

	bind_events: function () {
		var me = this;

		// Clear filters
		$("#clear_filters_btn").on("click", function () {
			Object.keys(me.filter_fields).forEach(function (key) {
				me.filter_fields[key].set_value("");
			});
			me.filter_values = {};
			me.current_start = 0;
			me.load_data();
		});

		// Save All
		this.$save_all_btn.on("click", function () {
			me.save_all_rows();
		});

		// Bulk update taster
		$("#bulk_update_taster_btn").on("click", function () {
			me.bulk_update_taster();
		});

		// Bulk update other fields (event delegation)
		$(".tea-eval-page")
			.off("click", ".btn-outline-primary[data-field]")
			.on("click", ".btn-outline-primary[data-field]", function (e) {
				var field = $(e.currentTarget).data("field");
				if (field) me.bulk_update_field(field);
			});

		// Page size
		$(".tea-eval-page")
			.off("click", ".eval-page-size")
			.on("click", ".eval-page-size", function (e) {
				$(".eval-page-size").removeClass("active");
				$(e.currentTarget).addClass("active");
				me.current_page_length = parseInt($(e.currentTarget).data("value"));
				me.current_start = 0;
				me.load_data();
			});

		// Pagination
		this.$prev_page_btn.on("click", function () {
			if (me.current_start > 0) {
				me.current_start = Math.max(0, me.current_start - me.current_page_length);
				me.load_data();
			}
		});

		this.$next_page_btn.on("click", function () {
			if (me.current_start + me.current_page_length < me.total_count) {
				me.current_start = me.current_start + me.current_page_length;
				me.load_data();
			}
		});

		// Export Excel
		$("#export_excel_btn").on("click", function () {
			me.export_to_excel();
		});
	},

	// -------------------------------------------------------------------------
	// FILTER COLLECTION
	// -------------------------------------------------------------------------

	collect_filters: function () {
		var me = this;
		this.filter_values = {};
		Object.keys(this.filter_fields).forEach(function (key) {
			var val = me.filter_fields[key].get_value();
			if (val && String(val).trim() !== "") {
				me.filter_values[key] = me.convert_date_to_iso(val.trim());
			}
		});
	},

	// -------------------------------------------------------------------------
	// BULK UPDATE
	// -------------------------------------------------------------------------

	bulk_update_taster: function () {
		var me = this;
		var $checked = $(".lot-select-checkbox:checked");
		if (!$checked.length) {
			frappe.msgprint(__("Please select at least one row to update."));
			return;
		}

		var d = new frappe.ui.Dialog({
			title: __("Update Taster"),
			fields: [
				{ fieldname: "taster", label: "Taster", fieldtype: "Link", options: "Taster" },
			],
			primary_action_label: __("Update"),
			primary_action: function () {
				var val = d.get_values().taster;
				if (!val) {
					frappe.msgprint(__("Please select a Taster."));
					return;
				}
				d.hide();
				me.bulk_update_selected("taster", val);
			},
		});
		d.show();
	},

	bulk_update_field: function (field) {
		var me = this;
		var $checked = $(".lot-select-checkbox:checked");
		if (!$checked.length) {
			frappe.msgprint(__("Please select at least one row to update."));
			return;
		}

		var field_config = this.get_field_config(field);
		if (!field_config) {
			frappe.msgprint(__("Unknown field: {0}", [field]));
			return;
		}

		var dialog_fields = [
			{
				fieldname: "value",
				label: field_config.label,
				fieldtype: field_config.fieldtype,
				options: field_config.options || undefined,
			},
		];

		var d = new frappe.ui.Dialog({
			title: __("Update {0}", [field_config.label]),
			fields: dialog_fields,
			primary_action_label: __("Update"),
			primary_action: function () {
				var val = d.get_values().value;
				if (val === undefined || val === null || val === "") {
					frappe.msgprint(__("Please enter a value."));
					return;
				}
				me.bulk_update_selected(field, val);
				d.hide();
			},
		});
		d.show();
	},

	bulk_update_selected: function (field, value) {
		var me = this;
		var $checked = $(".lot-select-checkbox:checked");
		var updated_count = 0;

		// Convert date values to display format for the table
		var display_value = value;
		if (field === "evaluation_date" && value) {
			display_value = this.convert_iso_to_display(value);
		}

		$checked.each(function () {
			var row_key = $(this).data("row-key");
			if (!row_key) return;
			var $cell = me.$table_container.find(
				'.eval-cell[data-row-key="' + row_key + '"][data-col="' + field + '"]'
			);
			if ($cell.length) {
				$cell.val(display_value);
				if (!me.edited_rows[row_key]) me.edited_rows[row_key] = {};
				me.edited_rows[row_key][field] = value;
				var $save_btn = me.$table_container.find(
					'.save-row-btn[data-row-key="' + row_key + '"]'
				);
				me.set_save_button_state($save_btn, "edited");
				updated_count++;

				// Update row class for visual feedback
				var $row = me.$table_container.find('tr[data-row-key="' + row_key + '"]');
				$row.addClass("row-edited");
			}
		});

		frappe.show_alert({
			message: __("{0} updated for {1} row(s).", [
				this.get_field_config(field).label,
				updated_count,
			]),
			indicator: "green",
		});
		this.update_save_all_count();
	},

	get_field_config: function (field) {
		var config_map = {
			stage: {
				label: "Stage",
				fieldtype: "Select",
				options: this.dropdown_options.stage ? this.dropdown_options.stage.join("\n") : "",
			},
			evaluation_date: { label: "Eval Date", fieldtype: "Date", options: null },
			liquor_mark: {
				label: "Liquor Mark",
				fieldtype: "Select",
				options: this.dropdown_options.liquor_mark
					? this.dropdown_options.liquor_mark.join("\n")
					: "",
			},
			suggested_valuation: { label: "Suggested Val", fieldtype: "Float", options: null },
			colour: { label: "Colour", fieldtype: "Int", options: null },
			strength: { label: "Strength", fieldtype: "Int", options: null },
			taste: { label: "Taste", fieldtype: "Int", options: null },
			briskness: { label: "Briskness", fieldtype: "Int", options: null },
			quality_grade: {
				label: "Quality Grade",
				fieldtype: "Select",
				options: this.dropdown_options.quality_grade
					? this.dropdown_options.quality_grade.join("\n")
					: "",
			},
			density: { label: "Density", fieldtype: "Float", options: null },
		};
		return config_map[field] || null;
	},

	// -------------------------------------------------------------------------
	// DATA LOADING
	// -------------------------------------------------------------------------

	load_data: function () {
		var me = this;
		this.$table_container.html(
			'<div class="eval-loading">' +
				get_spinner("32px") +
				"<div>Loading Tea Evaluations...</div></div>"
		);

		this.api_call(
			"get_evaluations",
			{
				filters: JSON.stringify(this.filter_values),
				start: this.current_start,
				page_length: this.current_page_length,
			},
			function (result) {
				console.log("API Response:", result);
				console.log("Stage:", result.stage_options);
				console.log("Liquor:", result.liquor_mark_options);
				console.log("Quality:", result.quality_grade_options);
				if (result) {
					me.all_evaluations = result.evaluations || [];
					me.total_count = result.total_count || 0;

					// Remove edited_rows for rows no longer in the current filtered set
					var current_names = new Set(
						me.all_evaluations.map(function (e) {
							return e.name;
						})
					);
					Object.keys(me.edited_rows).forEach(function (key) {
						if (!current_names.has(key)) delete me.edited_rows[key];
					});

					me.dropdown_options = {
						stage: result.stage_options || [],
						liquor_mark: result.liquor_mark_options || [],
						quality_grade: result.quality_grade_options || [],
					};

					me.update_filter_select_options();
					me.update_save_all_count();
					me.render_table();
					me.update_pagination_ui();
				} else {
					me.$table_container.html(
						'<div class="alert alert-info m-3">No data available.</div>'
					);
				}
			}
		);
	},

	// -------------------------------------------------------------------------
	// TABLE RENDERING
	// -------------------------------------------------------------------------

	render_table: function () {
		if (!this.all_evaluations.length) {
			this.$table_container.html(
				'<div class="alert alert-info m-3">No Tea Evaluations found.</div>'
			);
			return;
		}

		var html =
			'<div class="table-responsive"><table class="table table-bordered eval-table" id="eval_table"><thead><tr>';

		// Checkbox header
		html +=
			'<th class="eval-th-checkbox">' +
			'<input type="checkbox" id="select_all_lots" title="Select All" class="lot-select-checkbox form-check-input">' +
			"</th>";

		// Readonly column headers
		this.readonly_cols.forEach(function (col) {
			html +=
				'<th class="eval-th" style="min-width:' +
				col.width +
				'px;">' +
				frappe.utils.escape_html(col.label) +
				"</th>";
		});

		// Editable column headers
		this.editable_cols.forEach(function (col) {
			html +=
				'<th class="eval-th" style="min-width:' +
				col.width +
				'px;">' +
				frappe.utils.escape_html(col.label) +
				"</th>";
		});

		// Save column header
		html += '<th class="eval-th-save">Save</th>';
		html += "</tr></thead><tbody>";

		this.all_evaluations.forEach((evaluation, idx) => {
			html += this.build_row(evaluation, idx);
		});

		html += "</tbody></table></div>";
		this.$table_container.html(html);
		this.bind_table_events();
	},

	build_row: function (evaluation, idx) {
		var row_key = evaluation.name;
		var has_edits = !!this.edited_rows[row_key];
		var html = '<tr data-row-key="' + row_key + '" data-idx="' + idx + '">';

		// Checkbox cell
		html +=
			'<td class="eval-td-center">' +
			'<input type="checkbox" class="lot-select-checkbox form-check-input" data-row-key="' +
			row_key +
			'">' +
			"</td>";

		// Readonly cells
		this.readonly_cols.forEach(function (col) {
			var val = col.key === "idx" ? this.current_start + idx + 1 : evaluation[col.key] || "";
			if (col.clickable) {
				html +=
					'<td class="eval-td">' +
					'<a href="#" class="lot-id-link" data-lot-name="' +
					frappe.utils.escape_html(val) +
					'">' +
					frappe.utils.escape_html(String(val)) +
					"</a></td>";
			} else if (col.key === "stage") {
				html += '<td class="eval-td">' + this.get_stage_badge_html(val) + "</td>";
			} else {
				html += '<td class="eval-td">' + frappe.utils.escape_html(String(val)) + "</td>";
			}
		}, this);

		// Editable cells
		this.editable_cols.forEach(function (col) {
			var current_val = "";
			if (this.edited_rows[row_key] && this.edited_rows[row_key][col.key] !== undefined) {
				current_val = this.edited_rows[row_key][col.key];
			} else if (evaluation[col.key] !== undefined && evaluation[col.key] !== null) {
				current_val = evaluation[col.key];
			}

			html +=
				'<td class="eval-td-cell">' +
				this.get_editable_cell_html(col, row_key, String(current_val)) +
				"</td>";
		}, this);

		// Save button cell
		var save_class = has_edits ? "btn-warning" : "btn-success";
		var save_disabled = has_edits ? "" : "disabled";
		html +=
			'<td class="eval-td-center">' +
			'<button class="save-row-btn ' +
			save_class +
			'" data-row-key="' +
			row_key +
			'" ' +
			save_disabled +
			">" +
			get_icon("save", "12px") +
			"</button></td>";

		html += "</tr>";
		return html;
	},

	get_editable_cell_html: function (col, row_key, current_value) {
		var name_attr = 'data-col="' + col.key + '" data-row-key="' + row_key + '"';
		var val = current_value || "";

		switch (col.type) {
			case "select":
				var opts = this.dropdown_options[col.options_key] || [];
				var h = '<select class="eval-cell eval-select" ' + name_attr + ">";
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
					'<input type="text" class="eval-cell eval-link" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'" placeholder="Search..." autocomplete="off" />'
				);

			case "date":
				var display_val = this.convert_iso_to_display(val);
				return (
					'<div class="eval-date-wrapper">' +
					'<input type="text" class="eval-cell eval-date" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(display_val) +
					'" placeholder="dd-mm-yyyy" autocomplete="off" />' +
					'<button class="btn btn-outline-secondary btn-sm eval-date-btn" ' +
					'data-col="' +
					col.key +
					'" data-row-key="' +
					row_key +
					'" title="Select date">' +
					get_icon("calendar", "12px") +
					"</button></div>"
				);

			case "number":
				return (
					'<input type="number" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'" min="0" max="100" />'
				);

			case "currency":
			case "float":
				return (
					'<input type="number" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'" step="0.01" min="0" />'
				);

			default:
				return (
					'<input type="text" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'" autocomplete="off" />'
				);
		}
	},

	// -------------------------------------------------------------------------
	// TABLE EVENTS (Event Delegation)
	// -------------------------------------------------------------------------

	bind_table_events: function () {
		var me = this;
		var $container = this.$table_container;

		// Edit cell change
		$container
			.off("change input", ".eval-cell")
			.on("change input", ".eval-cell", function (e) {
				var $el = $(e.currentTarget);
				var row_key = $el.data("row-key");
				var col_key = $el.data("col");
				if (!row_key || !col_key) return;

				if (!me.edited_rows[row_key]) me.edited_rows[row_key] = {};
				me.edited_rows[row_key][col_key] = $el.val();

				var $save_btn = $container.find('.save-row-btn[data-row-key="' + row_key + '"]');
				me.set_save_button_state($save_btn, "edited");
				me.update_save_all_count();
			});

		// Link cell click - open selector dialog
		$container.off("click", ".eval-link").on("click", ".eval-link", function (e) {
			e.preventDefault();
			var $input = $(e.currentTarget);
			var col_key = $input.data("col");
			var col_def = me.editable_cols.find(function (c) {
				return c.key === col_key;
			});
			var doctype = col_def ? col_def.options : null;
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

		// Date button click
		$container.off("click", ".eval-date-btn").on("click", ".eval-date-btn", function (e) {
			var $btn = $(e.currentTarget);
			var row_key = $btn.data("row-key");
			var col = $btn.data("col");
			var $input = $container.find(
				'.eval-date[data-row-key="' + row_key + '"][data-col="' + col + '"]'
			);

			if (!$input.data("dp")) {
				$input
					.datepicker({
						language: "en",
						dateFormat: "dd-mm-yyyy",
						autoClose: true,
						onSelect: function () {
							$input.trigger("change");
						},
					})
					.data("datepicker");
			}
			$input.data("dp").show();
		});

		// Save row button click
		$container.off("click", ".save-row-btn").on("click", ".save-row-btn", function (e) {
			var $btn = $(e.currentTarget);
			var row_key = $btn.data("row-key");
			me.save_row(row_key, $btn);
		});

		// ID link click
		$container.off("click", ".lot-id-link").on("click", ".lot-id-link", function (e) {
			e.preventDefault();
			var lot_name = $(e.currentTarget).data("lot-name");
			if (lot_name) frappe.set_route("Form", "Tea Evaluation", lot_name);
		});

		// Select all checkbox
		$container
			.off("change", "#select_all_lots")
			.on("change", "#select_all_lots", function (e) {
				var checked = $(e.currentTarget).prop("checked");
				$(".lot-select-checkbox").prop("checked", checked);
			});

		// Individual checkbox
		$container
			.off("change", ".lot-select-checkbox")
			.on("change", ".lot-select-checkbox", function (e) {
				var total = $(".lot-select-checkbox").length;
				var checked = $(".lot-select-checkbox:checked").length;
				$("#select_all_lots").prop("checked", total === checked);
			});
	},

	// -------------------------------------------------------------------------
	// SAVE LOGIC
	// -------------------------------------------------------------------------

	save_row: function (row_key, $btn) {
		var me = this;
		this.set_save_button_state($btn, "saving");
		$btn.html(get_spinner("12px"));

		var row_data = this.build_row_data(row_key);
		var $row = this.$table_container.find('tr[data-row-key="' + row_key + '"]');

		frappe.call({
			method: this.API_BASE + ".update_evaluation",
			args: { evaluation_name: row_key, data: JSON.stringify(row_data) },
			callback: function (r) {
				if (r.message && r.message.success) {
					$btn.html(get_icon("save", "12px"));
					me.set_save_button_state($btn, "saved");
					delete me.edited_rows[row_key];
					me.update_save_all_count();
					$row.removeClass("row-edited").addClass("row-saved");
					setTimeout(function () {
						$row.removeClass("row-saved");
					}, 1500);
					frappe.show_alert({
						message: __("Evaluation {0} updated successfully.", [row_key]),
						indicator: "green",
					});
				} else {
					$btn.html(get_icon("save", "12px"));
					me.set_save_button_state($btn, "error");
					frappe.msgprint(
						__("Error: {0}", [r.message ? r.message.message : "Unknown error"])
					);
				}
			},
			error: function (r) {
				$btn.html(get_icon("save", "12px"));
				me.set_save_button_state($btn, "error");
				frappe.msgprint(__("Error updating evaluation. Please try again."));
				console.error("Save error:", r);
			},
		});
	},

	build_row_data: function (row_key) {
		var row_data = {};
		var me = this;

		this.editable_keys.forEach(function (key) {
			var $cell = me.$table_container.find(
				'.eval-cell[data-row-key="' + row_key + '"][data-col="' + key + '"]'
			);
			var val = "";
			if ($cell.length) {
				val = $cell.val();
			} else if (me.edited_rows[row_key] && me.edited_rows[row_key][key] !== undefined) {
				val = me.edited_rows[row_key][key];
			}

			if (key === "evaluation_date" && val) {
				row_data[key] = me.convert_date_to_iso(val);
			} else {
				row_data[key] = val;
			}
		});

		return row_data;
	},

	save_all_rows: function () {
		var me = this;
		var row_keys = Object.keys(this.edited_rows);
		if (!row_keys.length) {
			frappe.show_alert({
				message: __("No rows to save. Edit some fields first."),
				indicator: "orange",
			});
			return;
		}

		var $btn = this.$save_all_btn;
		this.set_save_button_state($btn, "saving");
		$btn.html(get_spinner("16px") + " Saving...");

		var bulk_data = {};
		row_keys.forEach(function (row_key) {
			bulk_data[row_key] = me.build_row_data(row_key);
		});

		frappe.call({
			method: this.API_BASE + ".bulk_update_evaluations",
			args: {
				evaluation_names: JSON.stringify(row_keys),
				data: JSON.stringify(bulk_data),
			},
			callback: function (r) {
				$btn.prop("disabled", false);
				$btn.html(get_icon("save_all", "16px") + " Save All");
				$btn.append(
					'<span class="badge bg-light text-dark ms-1" id="save_all_count" style="display:none;">0</span>'
				);
				me.$save_all_count = $("#save_all_count");

				if (r.message && r.message.success) {
					row_keys.forEach(function (row_key) {
						delete me.edited_rows[row_key];
						var $save_btn = me.$table_container.find(
							'.save-row-btn[data-row-key="' + row_key + '"]'
						);
						if ($save_btn.length) {
							$save_btn.html(get_icon("save", "12px"));
							me.set_save_button_state($save_btn, "saved");
						}
					});
					me.update_save_all_count();
					frappe.show_alert({ message: r.message.message, indicator: "green" });
				} else {
					frappe.show_alert({
						message: r.message ? r.message.message : "Bulk update failed.",
						indicator: "red",
					});
				}
			},
			error: function (r) {
				$btn.prop("disabled", false);
				$btn.html(get_icon("save_all", "16px") + " Save All");
				$btn.append(
					'<span class="badge bg-light text-dark ms-1" id="save_all_count">' +
						Object.keys(me.edited_rows).length +
						"</span>"
				);
				me.$save_all_count = $("#save_all_count");
				frappe.show_alert({
					message: __("Error saving evaluations. Please try again."),
					indicator: "red",
				});
				console.error("Bulk save error:", r);
			},
		});
	},

	update_save_all_count: function () {
		var count = Object.keys(this.edited_rows).length;
		if (count > 0) {
			this.$save_all_count.text(count).show();
		} else {
			this.$save_all_count.hide();
		}
	},

	// -------------------------------------------------------------------------
	// EXPORT
	// -------------------------------------------------------------------------

	export_to_excel: function () {
		var me = this;
		var $btn = $("#export_excel_btn");
		var original_html = $btn.html();
		$btn.prop("disabled", true).html(get_spinner("14px") + " Exporting...");

		this.collect_filters();

		frappe.call({
			method: this.API_BASE + ".export_evaluations",
			args: { filters: JSON.stringify(this.filter_values) },
			callback: function (r) {
				$btn.prop("disabled", false).html(original_html);

				if (r.message && r.message.content) {
					try {
						var binaryString = atob(r.message.content);
						var bytes = new Uint8Array(binaryString.length);
						for (var i = 0; i < binaryString.length; i++) {
							bytes[i] = binaryString.charCodeAt(i);
						}

						var blob = new Blob([bytes.buffer], {
							type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
						});
						var url = window.URL.createObjectURL(blob);
						var a = document.createElement("a");
						a.href = url;
						a.download = r.message.filename || "tea_evaluation.xlsx";
						document.body.appendChild(a);
						a.click();
						document.body.removeChild(a);
						window.URL.revokeObjectURL(url);

						frappe.show_alert({
							message: __("Excel file exported successfully."),
							indicator: "green",
						});
					} catch (e) {
						console.error("Error decoding Excel file:", e);
						frappe.msgprint(__("Error processing Excel file. Please try again."));
					}
				} else {
					frappe.msgprint(__("No data available to export."));
				}
			},
			error: function (r) {
				$btn.prop("disabled", false).html(original_html);
				frappe.msgprint(__("Error exporting data. Please try again."));
				console.error("Export error:", r);
			},
		});
	},

	// -------------------------------------------------------------------------
	// PAGINATION UI
	// -------------------------------------------------------------------------

	update_pagination_ui: function () {
		var end = Math.min(this.current_start + this.current_page_length, this.total_count);
		if (this.total_count > 0) {
			this.$pagination_info.text(
				"Showing " +
					(this.current_start + 1) +
					" to " +
					end +
					" of " +
					this.total_count +
					" entries"
			);
		} else {
			this.$pagination_info.text("No entries found");
		}
		this.$prev_page_btn.prop("disabled", this.current_start === 0);
		this.$next_page_btn.prop("disabled", end >= this.total_count);
	},

	// -------------------------------------------------------------------------
	// HELPERS
	// -------------------------------------------------------------------------

	api_call: function (method, args, callback) {
		frappe.call({
			method: this.API_BASE + "." + method,
			args: args,
			callback: function (r) {
				callback(r.message);
			},
			error: function (r) {
				console.error("API error:", method, r);
				callback(null);
			},
		});
	},

	convert_date_to_iso: function (date_str) {
		if (!date_str) return "";
		// If already in ISO format (yyyy-mm-dd), return as-is
		if (/^\d{4}-\d{2}-\d{2}$/.test(date_str)) {
			return date_str;
		}
		// Convert from display format (dd-mm-yyyy) to ISO (yyyy-mm-dd)
		var parts = date_str.split("-");
		if (parts.length === 3) {
			return parts[2] + "-" + parts[1] + "-" + parts[0];
		}
		return date_str;
	},

	convert_iso_to_display: function (iso_date) {
		if (!iso_date) return "";
		// If already in display format (dd-mm-yyyy), return as-is
		if (/^\d{2}-\d{2}-\d{4}$/.test(iso_date)) {
			return iso_date;
		}
		// Convert from ISO format (yyyy-mm-dd) to display (dd-mm-yyyy)
		var parts = iso_date.split("-");
		if (parts.length === 3) {
			return parts[2] + "-" + parts[1] + "-" + parts[0];
		}
		return iso_date;
	},

	set_save_button_state: function ($btn, state) {
		switch (state) {
			case "saved":
				$btn.removeClass("btn-warning btn-danger")
					.addClass("btn-success")
					.prop("disabled", true);
				break;
			case "edited":
				$btn.removeClass("btn-success btn-danger")
					.addClass("btn-warning")
					.prop("disabled", false);
				break;
			case "saving":
				$btn.prop("disabled", true);
				break;
			case "error":
				$btn.removeClass("btn-success btn-warning")
					.addClass("btn-danger")
					.prop("disabled", false);
				break;
		}
	},
};
