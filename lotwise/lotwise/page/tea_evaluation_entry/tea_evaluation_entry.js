// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.pages["tea-evaluation-entry"].on_page_load = function (wrapper) {
	new TeaEvaluationEntry(wrapper);
};

// =============================================================================
// ICONS & SPINNER
// =============================================================================

const WS_ICONS = {
	filter: '<path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>',
	clear: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
	taster: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>',
	edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4L16.5 3.5z"/>',
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
	new_eval: '<path d="M12 5v14M5 12h14"/>',
	sort_desc:
		'<path d="M11 5h10"/><path d="M11 9h7"/><path d="M11 13h4"/><path d="M3 17l3 3 3-3"/><path d="M6 18V4"/>',
	sort_asc:
		'<path d="M11 5h10"/><path d="M11 9h7"/><path d="M11 13h4"/><path d="M3 7l3-3 3 3"/><path d="M6 4v14"/>',
};

function get_ws_icon(name, size) {
	size = size || "14px";
	return (
		'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:' +
		size +
		";height:" +
		size +
		';vertical-align:middle;">' +
		(WS_ICONS[name] || "") +
		"</svg>"
	);
}

function get_ws_spinner(size) {
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
// Tea Evaluation Entry Page
// =============================================================================

function TeaEvaluationEntry(wrapper) {
	this.wrapper = wrapper;
	this.page = null;
	this.mode = "new";

	// State
	this.records = [];
	this.dropdown_options = { stage: [], liquor_mark: [], quality_grade: [] };
	this.edited_rows = {};
	this.current_start = 0;
	this.current_page_length = 20;
	this.total_count = 0;
	this.filter_values = {};
	this.filter_fields = {};
	this.sort_order = "desc";
	this.saved_rows = {};
	this.load_token = 0;
	this.clearing = false;

	// Default values
	this.default_taster = "";
	this.default_eval_date = "";
	this.default_stage = "";

	// DOM Cache
	this.$table_container = null;
	this.$save_all_btn = null;
	this.$save_all_count = null;
	this.$prev_page_btn = null;
	this.$next_page_btn = null;
	this.$pagination_info = null;

	// Constants
	this.API_BASE = "lotwise.lotwise.page.tea_evaluation_entry.tea_evaluation_entry";

	// Column definitions
	this.new_cols_readonly = [
		{ key: "idx", label: "#", width: 35 },
		{ key: "name", label: "Tea Lot ID", width: 160, clickable: true },
		{ key: "lot_no", label: "Lot No", width: 100 },
		{ key: "sale_no", label: "Sale No", width: 70 },
		{ key: "mark", label: "Mark", width: 80 },
		{ key: "grade", label: "Grade", width: 80 },
		{ key: "invoice_number", label: "Invoice No", width: 100 },
		{ key: "auction_centre", label: "Auction Centre", width: 100 },
	];

	this.editable_cols = [
		{ key: "taster", label: "Taster", type: "link", options: "Taster", width: 100 },
		{
			key: "evaluation_stage",
			label: "Evaluation Stage",
			type: "link",
			options: "Evaluation Stage",
			width: 130,
		},
		{
			key: "liquor_mark",
			label: "Liquor Mark",
			type: "link",
			options: "Liquor Mark",
			width: 100,
		},
		{ key: "evaluation_date", label: "Eval Date", type: "date", width: 120 },
		{ key: "suggested_valuation", label: "Suggested Val", type: "currency", width: 100 },
		{ key: "actual_valuation", label: "Actual Val", type: "currency", width: 100 },
		{ key: "colour", label: "Colour", type: "number", width: 60 },
		{ key: "strength", label: "Strength", type: "number", width: 70 },
		{ key: "taste", label: "Taste", type: "number", width: 60 },
		{ key: "briskness", label: "Briskness", type: "number", width: 70 },
		{
			key: "quality_grade",
			label: "Quality Grade",
			type: "link",
			options: "Quality Grade",
			width: 105,
		},
		{ key: "density", label: "Density", type: "float", width: 70 },
		{ key: "remarks", label: "Remarks", type: "data", width: 150 },
	];

	this.editable_keys = [
		"taster",
		"evaluation_stage",
		"liquor_mark",
		"evaluation_date",
		"suggested_valuation",
		"actual_valuation",
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

TeaEvaluationEntry.prototype = {
	constructor: TeaEvaluationEntry,

	// -------------------------------------------------------------------------
	// HELPERS
	// -------------------------------------------------------------------------

	get_stage_badge_html: function (stage) {
		if (!stage) return "";
		var s = String(stage).toLowerCase().trim();
		var css_class = "";
		if (s === "draft" || s === "in stock" || s === "available") {
			css_class = "ws-stage-draft";
		} else if (s === "pending" || s === "under evaluation") {
			css_class = "ws-stage-pending";
		} else if (s === "approved" || s === "sold" || s === "completed") {
			css_class = "ws-stage-approved";
		} else if (s === "rejected" || s === "cancelled" || s === "void") {
			css_class = "ws-stage-rejected";
		} else {
			css_class = "ws-stage-draft";
		}
		return (
			'<span class="ws-stage-badge ' +
			css_class +
			'">' +
			frappe.utils.escape_html(stage) +
			"</span>"
		);
	},

	esc: function (value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	},

	fmt: function (value) {
		return Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
	},

	// -------------------------------------------------------------------------
	// INIT
	// -------------------------------------------------------------------------

	init: function () {
		this.page = frappe.ui.make_app_page({
			parent: this.wrapper,
			title: __("Tea Evaluation Entry"),
			single_column: true,
		});

		this.build_page();
		this.create_filter_fields();
		this.bind_events();

		this.load_data();

		this.page.add_inner_button(__("New Tea Evaluation"), () => {
			frappe.new_doc("Tea Evaluation");
		});

		this.page.add_inner_button(__("Tea Evaluation Comparison"), () => {
			frappe.set_route("query-report", "Tea Evaluation Comparison");
		});
	},

	// -------------------------------------------------------------------------
	// BUILD PAGE
	// -------------------------------------------------------------------------

	build_page: function () {
		$(this.page.main).html(`
			<div class="ws-page">
				<!-- FILTERS CARD -->
				<div class="card mb-2 shadow-sm rounded">
					<div class="card-header py-2">
						<span class="d-flex align-items-center gap-1">
							${get_ws_icon("filter", "16px")} Filters
						</span>
					</div>
					<div class="card-body py-2">
					<div class="row g-2 align-items-end ws-filter-grid">
						<div class="col ws-field">
							<label class="ws-field-label">Acquisition Channel</label>
							<div id="ws_filter_acquisition_channel_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Tea Lot</label>
							<div id="ws_filter_tea_lot_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Sale No</label>
							<div id="ws_filter_sale_no_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Lot No</label>
							<div id="ws_filter_lot_no_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Invoice No</label>
							<div id="ws_filter_invoice_number_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Mark</label>
							<div id="ws_filter_mark_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Grade</label>
							<div id="ws_filter_grade_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Evaluation Status</label>
							<div id="ws_filter_evaluation_status_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Auction Centre</label>
							<div id="ws_filter_auction_centre_field"></div>
						</div>
						<div class="col ws-field">
							<label class="ws-field-label">Purchase Status</label>
							<div id="ws_filter_purchase_status_field"></div>
						</div>
						<div class="col-auto align-self-end ws-field-btn">
							<button class="btn btn-outline-secondary btn-sm" id="ws_clear_filters_btn">
								${get_ws_icon("clear", "14px")} Clear
							</button>
						</div>
						</div>
					</div>
				</div>

				<!-- DEFAULT VALUES CARD -->
				<div class="card mb-2 shadow-sm rounded" id="ws_defaults_card">
					<div class="card-header py-2">
						<span class="d-flex align-items-center gap-1">
							${get_ws_icon("edit", "16px")} Default Evaluation Values
						</span>
					</div>
					<div class="card-body py-2">
						<div class="ws-defaults-row">
							<div class="ws-field">
								<label class="ws-field-label">Taster</label>
								<input type="text" class="form-control form-control-sm" id="ws_default_taster" placeholder="Select Taster" autocomplete="off" />
							</div>
							<div class="ws-field">
								<label class="ws-field-label">Evaluation Date</label>
								<div class="ws-input-group">
									<input type="text" class="form-control form-control-sm" id="ws_default_eval_date" placeholder="dd-mm-yyyy" autocomplete="off" />
									<button class="ws-input-btn" id="ws_default_eval_date_btn" title="Select date">
										${get_ws_icon("calendar", "14px")}
									</button>
								</div>
							</div>
							<div class="ws-field">
								<label class="ws-field-label">Stage</label>
								<select class="form-control form-control-sm" id="ws_default_stage">
									<option value=""></option>
								</select>
							</div>
							<div class="ws-field ws-field-btn">
								<button class="btn btn-success btn-sm fw-semibold" id="ws_save_all_btn">
									${get_ws_icon("save_all", "16px")} Save All
									<span class="badge bg-light text-dark ms-1" id="ws_save_all_count" style="display:none;">0</span>
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- TOOLBAR -->
				<div class="mb-2">
					<div class="d-flex flex-wrap gap-1 align-items-center">
						<button class="btn btn-outline-primary btn-sm" id="ws_bulk_taster_btn">
							${get_ws_icon("taster", "14px")} Taster
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="evaluation_date">
							${get_ws_icon("calendar", "14px")} Eval Date
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="evaluation_stage">
							${get_ws_icon("edit", "14px")} Stage
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="liquor_mark">
							${get_ws_icon("edit", "14px")} Liquor Mark
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="suggested_valuation">
							${get_ws_icon("valuation", "14px")} Suggested Val
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="actual_valuation">
							${get_ws_icon("valuation", "14px")} Actual Val
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="colour">
							${get_ws_icon("colour", "14px")} Colour
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="strength">
							${get_ws_icon("strength", "14px")} Strength
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="taste">
							${get_ws_icon("taste", "14px")} Taste
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="briskness">
							${get_ws_icon("briskness", "14px")} Briskness
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="quality_grade">
							${get_ws_icon("quality", "14px")} Quality Grade
						</button>
						<button class="btn btn-outline-primary btn-sm" data-field="density">
							${get_ws_icon("density", "14px")} Density
						</button>
						<button class="btn btn-outline-success btn-sm fw-semibold" id="ws_export_btn">
							${get_ws_icon("export", "14px")} Export Excel
						</button>
						<button class="btn btn-outline-secondary btn-sm" id="ws_sort_order_btn" title="Sort: Newest">
							${get_ws_icon("sort_desc", "14px")} <span id="ws_sort_order_label">Newest</span>
						</button>
					</div>
				</div>

				<!-- TABLE CARD -->
				<div class="card mb-2 shadow-sm rounded">
					<div class="card-body p-0">
						<div id="ws_table_container" class="ws-loading">
							${get_ws_spinner("32px")}
							<div>Loading data...</div>
						</div>
					</div>
					<div class="card-footer py-2">
						<div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
							<span class="text-muted small" id="ws_pagination_info">No entries found</span>
							<div class="d-flex align-items-center gap-2">
								<div class="btn-group" role="group">
									<button class="btn btn-outline-secondary btn-sm ws-page-size" data-value="20">20</button>
									<button class="btn btn-outline-secondary btn-sm ws-page-size" data-value="100">100</button>
									<button class="btn btn-outline-secondary btn-sm ws-page-size" data-value="500">500</button>
									<button class="btn btn-outline-secondary btn-sm ws-page-size" data-value="2500">2500</button>
								</div>
								<div class="btn-group" role="group">
									<button class="btn btn-outline-primary btn-sm" id="ws_prev_page_btn" disabled>
										${get_ws_icon("prev", "14px")}
									</button>
									<button class="btn btn-outline-primary btn-sm" id="ws_next_page_btn">
										${get_ws_icon("next", "14px")}
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		// Cache DOM
		this.$table_container = $("#ws_table_container");
		this.$save_all_btn = $("#ws_save_all_btn");
		this.$save_all_count = $("#ws_save_all_count");
		this.$prev_page_btn = $("#ws_prev_page_btn");
		this.$next_page_btn = $("#ws_next_page_btn");
		this.$pagination_info = $("#ws_pagination_info");

		this.$save_all_count.hide();
		$(".ws-page-size[data-value='20']").addClass("active");

		// Load CSS
		this.load_css();
	},

	load_css: function () {
		if ($("#ws-custom-css").length) return;
		$("<link>", {
			id: "ws-custom-css",
			rel: "stylesheet",
			href: "/assets/lotwise/lotwise/page/tea_evaluation_entry/tea_evaluation_entry.css",
		}).appendTo("head");
	},

	// -------------------------------------------------------------------------
	// FILTER FIELDS (Frappe Native Controls)
	// -------------------------------------------------------------------------

	create_filter_fields: function () {
		var me = this;
		var configs = [
			{
				fieldname: "acquisition_channel",
				label: "Acquisition Channel",
				fieldtype: "Select",
				options: "\nAuction\nPrivate\nOutsourced",
			},
			{ fieldname: "tea_lot", label: "Tea Lot", fieldtype: "Link", options: "Tea Lot" },
			{ fieldname: "sale_no", label: "Sale No", fieldtype: "Data" },
			{ fieldname: "lot_no", label: "Lot No", fieldtype: "Data" },
			{ fieldname: "invoice_number", label: "Invoice No", fieldtype: "Data" },
			{ fieldname: "mark", label: "Mark", fieldtype: "Link", options: "Mark" },
			{ fieldname: "grade", label: "Grade", fieldtype: "Link", options: "Grade" },
			{
				fieldname: "evaluation_status",
				label: "Evaluation Status",
				fieldtype: "Link",
				options: "Evaluation Status",
			},
			{
				fieldname: "auction_centre",
				label: "Auction Centre",
				fieldtype: "Link",
				options: "Auction Centre",
			},
			{
				fieldname: "purchase_status",
				label: "Purchase Status",
				fieldtype: "Link",
				options: "Purchase Status",
			},
		];

		configs.forEach(function (cfg) {
			var df = {
				fieldname: cfg.fieldname,
				label: cfg.label,
				fieldtype: cfg.fieldtype,
				options: cfg.options,
				change: function () {
					if (me.clearing) return;
					me.collect_filters();
					me.current_start = 0;
					me.load_data();
				},
			};
			var field = frappe.ui.form.make_control({
				parent: $("#ws_filter_" + cfg.fieldname + "_field"),
				df: df,
				render_input: true,
			});
			field.refresh();
			me.filter_fields[cfg.fieldname] = field;
		});
	},

	update_filter_select_options: function () {
		// No select-based filters remain; evaluation_stage/liquor_mark/quality_grade are Link fields
	},

	// -------------------------------------------------------------------------
	// EVENT BINDING
	// -------------------------------------------------------------------------

	bind_events: function () {
		var me = this;

		// Clear filters
		$("#ws_clear_filters_btn").on("click", function () {
			me.clearing = true;
			Object.keys(me.filter_fields).forEach(function (key) {
				me.filter_fields[key].set_value("");
			});
			me.clearing = false;
			me.filter_values = {};
			me.current_start = 0;
			me.load_data();
		});

		// Default taster
		$("#ws_default_taster").on("click", function () {
			var $input = $(this);
			var d = new frappe.ui.Dialog({
				title: __("Select Taster"),
				fields: [
					{ fieldname: "taster", label: "Taster", fieldtype: "Link", options: "Taster" },
				],
				primary_action_label: __("Select"),
				primary_action: function () {
					var val = d.get_values().taster;
					if (val) {
						$input.val(val);
						me.default_taster = val;
						me.apply_default_taster();
					}
					d.hide();
				},
			});
			d.show();
		});
		$("#ws_default_taster").on("change", function () {
			me.default_taster = $(this).val();
			me.apply_default_taster();
		});

		// Default eval date
		$("#ws_default_eval_date").on("change input", function () {
			me.default_eval_date = $(this).val();
			me.apply_defaults();
		});
		$("#ws_default_eval_date_btn").on("click", function () {
			var $input = $("#ws_default_eval_date");
			if (!$input.data("dp")) {
				var dp = $input
					.datepicker({
						language: "en",
						dateFormat: "dd-mm-yyyy",
						autoClose: true,
						onSelect: function () {
							$input.trigger("change");
						},
					})
					.data("datepicker");
				$input.data("dp", dp);
			}
			$input.data("dp").show();
		});

		// Default stage
		$("#ws_default_stage").on("change", function () {
			me.default_stage = $(this).val();
			me.apply_defaults();
		});

		// Save All
		this.$save_all_btn.on("click", function () {
			me.save_all_rows();
		});

		// Bulk update taster
		$("#ws_bulk_taster_btn").on("click", function () {
			me.bulk_update_dialog("taster");
		});

		// Bulk update other fields
		$(".ws-page")
			.off("click", ".btn-outline-primary[data-field]")
			.on("click", ".btn-outline-primary[data-field]", function () {
				var field = $(this).data("field");
				if (field) me.bulk_update_dialog(field);
			});

		// Page size
		$(".ws-page")
			.off("click", ".ws-page-size")
			.on("click", ".ws-page-size", function () {
				$(".ws-page-size").removeClass("active");
				$(this).addClass("active");
				me.current_page_length = parseInt($(this).data("value"));
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

		// Export
		$("#ws_export_btn").on("click", function () {
			me.export_data();
		});

		// Sort order toggle
		$("#ws_sort_order_btn").on("click", function () {
			me.sort_order = me.sort_order === "desc" ? "asc" : "desc";
			me.update_sort_order_btn();
			me.current_start = 0;
			me.load_data();
		});
	},

	update_sort_order_btn: function () {
		var is_desc = this.sort_order === "desc";
		var label = is_desc ? "Newest" : "Oldest";
		$("#ws_sort_order_btn")
			.attr("title", "Sort: " + label)
			.html(
				get_ws_icon(is_desc ? "sort_desc" : "sort_asc", "14px") +
					' <span id="ws_sort_order_label">' +
					label +
					"</span>"
			);
	},

	// -------------------------------------------------------------------------
	// DEFAULT VALUES
	// -------------------------------------------------------------------------

	apply_default_taster: function (mark_edited) {
		var me = this;
		if (!this.default_taster) return;
		mark_edited = mark_edited !== false;
		var $container = this.$table_container;
		$container.find('.ws-cell[data-col="taster"]').each(function () {
			var $cell = $(this);
			if (!mark_edited && $cell.val()) return;
			$cell.val(me.default_taster);
			var row_key = $cell.data("row-key");
			if (mark_edited && row_key) {
				if (!me.edited_rows[row_key]) me.edited_rows[row_key] = {};
				me.edited_rows[row_key]["taster"] = me.default_taster;
			}
		});
		if (!mark_edited) return;
		// Enable save buttons
		$container.find(".ws-save-row-btn").each(function () {
			var $btn = $(this);
			var key = $btn.data("row-key");
			if (key && me.edited_rows[key] && Object.keys(me.edited_rows[key]).length > 0) {
				$btn.prop("disabled", false).removeClass("btn-success").addClass("btn-warning");
			}
		});
		me.update_save_all_count();
	},

	apply_defaults: function () {
		var me = this;
		var $container = this.$table_container;

		if (this.default_taster) {
			$container.find('.ws-cell[data-col="taster"]').each(function () {
				var $cell = $(this);
				var key = $cell.data("row-key");
				if (key && me.edited_rows[key] && me.edited_rows[key]["taster"] !== undefined)
					return;
				$cell.val(me.default_taster);
				if (key) {
					if (!me.edited_rows[key]) me.edited_rows[key] = {};
					me.edited_rows[key]["taster"] = me.default_taster;
				}
			});
		}

		if (this.default_eval_date) {
			$container.find('.ws-cell[data-col="evaluation_date"]').each(function () {
				var $cell = $(this);
				var key = $cell.data("row-key");
				$cell.val(me.default_eval_date);
				if (key) {
					if (!me.edited_rows[key]) me.edited_rows[key] = {};
					me.edited_rows[key]["evaluation_date"] = me.convert_display_to_iso(
						me.default_eval_date
					);
				}
			});
		}

		if (this.default_stage) {
			$container.find('.ws-cell[data-col="evaluation_stage"]').each(function () {
				var $cell = $(this);
				var key = $cell.data("row-key");
				$cell.val(me.default_stage);
				if (key) {
					if (!me.edited_rows[key]) me.edited_rows[key] = {};
					me.edited_rows[key]["evaluation_stage"] = me.default_stage;
				}
			});
		}

		$container.find(".ws-save-row-btn").each(function () {
			var $btn = $(this);
			var key = $btn.data("row-key");
			if (key && me.edited_rows[key] && Object.keys(me.edited_rows[key]).length > 0) {
				$btn.prop("disabled", false).removeClass("btn-success").addClass("btn-warning");
			}
		});
		me.update_save_all_count();
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
				me.filter_values[key] = String(val).trim();
			}
		});
	},

	convert_date_to_iso: function (date_str) {
		if (!date_str) return "";
		if (/^\d{4}-\d{2}-\d{2}$/.test(date_str)) return date_str;
		var parts = date_str.split(/[-\/]/);
		if (parts.length === 3) {
			// dd/mm/yyyy or dd-mm-yyyy -> yyyy-mm-dd
			return parts[2] + "-" + parts[1] + "-" + parts[0];
		}
		return date_str;
	},

	convert_iso_to_display: function (iso_date) {
		if (!iso_date) return "";
		if (/^\d{2}[-\/]\d{2}[-\/]\d{4}$/.test(iso_date)) return iso_date;
		var parts = iso_date.split("-");
		if (parts.length === 3) {
			return parts[2] + "-" + parts[1] + "-" + parts[0];
		}
		return iso_date;
	},

	convert_display_to_iso: function (display_date) {
		if (!display_date) return "";
		if (/^\d{4}-\d{2}-\d{2}$/.test(display_date)) return display_date;
		var parts = display_date.split(/[-\/]/);
		if (parts.length === 3) {
			return parts[2] + "-" + parts[1] + "-" + parts[0];
		}
		return display_date;
	},

	// -------------------------------------------------------------------------
	// BULK UPDATE
	// -------------------------------------------------------------------------

	bulk_update_dialog: function (field) {
		var me = this;
		var $checked = $(".ws-select-checkbox[data-row-key]:checked");
		if (!$checked.length) {
			frappe.msgprint(__("Please select at least one row."));
			return;
		}

		var field_config = this.get_bulk_field_config(field);
		if (!field_config) {
			frappe.msgprint(__("Unknown field: {0}", [field]));
			return;
		}

		var d = new frappe.ui.Dialog({
			title: __("Update {0}", [field_config.label]),
			fields: [
				{
					fieldname: "value",
					label: field_config.label,
					fieldtype: field_config.fieldtype,
					options: field_config.options,
				},
			],
			primary_action_label: __("Update"),
			primary_action: function () {
				var val = d.get_values().value;
				if (val === undefined || val === null || val === "") {
					frappe.msgprint(__("Please enter a value."));
					return;
				}
				me.apply_bulk_update(field, val);
				d.hide();
			},
		});
		d.show();
	},

	get_bulk_field_config: function (field) {
		var map = {
			taster: { label: "Taster", fieldtype: "Link", options: "Taster" },
			evaluation_stage: {
				label: "Evaluation Stage",
				fieldtype: "Link",
				options: "Evaluation Stage",
			},
			evaluation_date: { label: "Eval Date", fieldtype: "Date" },
			liquor_mark: { label: "Liquor Mark", fieldtype: "Link", options: "Liquor Mark" },
			suggested_valuation: { label: "Suggested Val", fieldtype: "Float" },
			actual_valuation: { label: "Actual Val", fieldtype: "Float" },
			colour: { label: "Colour", fieldtype: "Int" },
			strength: { label: "Strength", fieldtype: "Int" },
			taste: { label: "Taste", fieldtype: "Int" },
			briskness: { label: "Briskness", fieldtype: "Int" },
			quality_grade: {
				label: "Quality Grade",
				fieldtype: "Link",
				options: "Quality Grade",
			},
			density: { label: "Density", fieldtype: "Float" },
		};
		return map[field] || null;
	},

	apply_bulk_update: function (field, value) {
		var me = this;
		var $checked = $(".ws-select-checkbox[data-row-key]:checked");
		var display_val = value;
		if (field === "evaluation_date" && value) {
			display_val = this.convert_iso_to_display(value);
		}

		$checked.each(function () {
			var key = $(this).data("row-key");
			if (!key) return;
			var $cell = me.$table_container.find(
				'.ws-cell[data-row-key="' + key + '"][data-col="' + field + '"]'
			);
			if ($cell.length) {
				$cell.val(display_val);
				if (!me.edited_rows[key]) me.edited_rows[key] = {};
				me.edited_rows[key][field] = value;
				var $btn = me.$table_container.find(
					'.ws-save-row-btn[data-row-key="' + key + '"]'
				);
				me.set_save_btn_state($btn, "edited");
				me.$table_container.find('tr[data-row-key="' + key + '"]').addClass("row-edited");
			}
		});

		frappe.show_alert({
			message: __("Updated for {0} row(s).", [$checked.length]),
			indicator: "green",
		});
		this.update_save_all_count();
	},

	// -------------------------------------------------------------------------
	// DATA LOADING
	// -------------------------------------------------------------------------

	load_data: function () {
		var me = this;
		this.$table_container.html(
			'<div class="ws-loading">' +
				get_ws_spinner("32px") +
				"<div>Loading data...</div></div>"
		);

		var token = ++this.load_token;
		this.api_call(
			"get_workspace_data",
			{
				// mode is always "new" on this page
				filters: JSON.stringify(this.filter_values),
				start: this.current_start,
				page_length: this.current_page_length,
				sort_order: this.sort_order,
			},
			function (result) {
				if (token !== me.load_token) return; // stale response
				if (result) {
					me.records = result.records || [];
					me.total_count = result.total_count || 0;

					// Clean up edited rows
					var current_names = new Set(
						me.records.map(function (r) {
							return r.name;
						})
					);
					Object.keys(me.edited_rows).forEach(function (k) {
						if (!current_names.has(k)) delete me.edited_rows[k];
					});

					me.dropdown_options = {
						stage: result.stage_options || [],
						liquor_mark: result.liquor_mark_options || [],
						quality_grade: result.quality_grade_options || [],
					};

					me.update_filter_select_options();
					me.update_default_stage_options();
					me.update_save_all_count();
					me.render_table();
					me.update_pagination();

					// Auto-fill taster if logged-in user is linked to a Taster record
					if (result.default_taster && !me.default_taster) {
						me.default_taster = result.default_taster;
						$("#ws_default_taster").val(result.default_taster);
					}
					// Fill empty taster cells without marking rows as edited
					me.apply_default_taster(false);
				} else {
					me.$table_container.html(
						'<div class="alert alert-info m-3">No data available.</div>'
					);
				}
			}
		);
	},

	update_default_stage_options: function () {
		var me = this;
		var $select = $("#ws_default_stage");
		var current = $select.val();
		$select.empty().append('<option value=""></option>');
		this.dropdown_options.stage.forEach(function (opt) {
			$select.append('<option value="' + me.esc(opt) + '">' + me.esc(opt) + "</option>");
		});
		if (current) $select.val(current);
	},

	// -------------------------------------------------------------------------
	// TABLE RENDERING
	// -------------------------------------------------------------------------

	render_table: function () {
		var me = this;
		if (!this.records.length) {
			this.$table_container.html(
				'<div class="alert alert-info m-3">No records found.</div>'
			);
			return;
		}

		var readonly_cols = this.new_cols_readonly;

		var html =
			'<div class="table-responsive"><table class="table table-bordered ws-table" id="ws_table"><thead><tr>';
		html +=
			'<th class="ws-th-checkbox ws-frozen-col" data-frozen-index="0"><input type="checkbox" id="ws_select_all" class="ws-select-checkbox form-check-input"></th>';

		readonly_cols.forEach(function (col, idx) {
			// Freeze all readonly columns
			var frozen_index = idx + 1;
			var frozen_class = " ws-frozen-col";
			var frozen_attr = ' data-frozen-index="' + frozen_index + '"';
			html +=
				'<th class="eval-th' +
				frozen_class +
				'"' +
				frozen_attr +
				' style="min-width:' +
				col.width +
				'px;">' +
				me.esc(col.label) +
				"</th>";
		});

		this.editable_cols.forEach(function (col) {
			html +=
				'<th class="eval-th" style="min-width:' +
				col.width +
				'px;">' +
				me.esc(col.label) +
				"</th>";
		});

		html += '<th class="ws-th-save">Save</th></tr></thead><tbody>';

		this.records.forEach(function (rec, idx) {
			html += me.build_row(rec, idx, true);
		});

		html += "</tbody></table></div>";
		this.$table_container.html(html);
		this.bind_table_events();
	},

	build_row: function (record, idx, is_new) {
		var me = this;
		var row_key = record.name;
		var has_edits = !!this.edited_rows[row_key];
		var html = '<tr data-row-key="' + row_key + '" data-idx="' + idx + '">';

		// Checkbox (frozen as index 0)
		html +=
			'<td class="ws-td-center ws-frozen-col" data-frozen-index="0"><input type="checkbox" class="ws-select-checkbox form-check-input" data-row-key="' +
			row_key +
			'"></td>';

		// Readonly columns
		var readonly_cols = this.new_cols_readonly;
		readonly_cols.forEach(function (col, col_idx) {
			var val = col.key === "idx" ? me.current_start + idx + 1 : record[col.key] || "";
			// Freeze all readonly columns
			// checkbox is frozen-index 0, so readonly columns start at index 1
			var frozen_class = " ws-frozen-col";
			var frozen_attr = ' data-frozen-index="' + (col_idx + 1) + '"';
			if (col.clickable) {
				var doctype = "Tea Lot";
				html +=
					'<td class="ws-td' +
					frozen_class +
					'"' +
					frozen_attr +
					'><a href="#" class="ws-id-link" data-doctype="' +
					doctype +
					'" data-name="' +
					me.esc(val) +
					'">' +
					me.esc(String(val)) +
					"</a></td>";
			} else if (col.key === "stage") {
				html +=
					'<td class="ws-td' +
					frozen_class +
					'"' +
					frozen_attr +
					">" +
					me.get_stage_badge_html(val) +
					"</td>";
			} else {
				html +=
					'<td class="ws-td' +
					frozen_class +
					'"' +
					frozen_attr +
					">" +
					me.esc(String(val)) +
					"</td>";
			}
		});

		// Editable columns
		this.editable_cols.forEach(function (col) {
			var current_val = "";
			if (me.edited_rows[row_key] && me.edited_rows[row_key][col.key] !== undefined) {
				current_val = me.edited_rows[row_key][col.key];
			} else if (record[col.key] !== undefined && record[col.key] !== null) {
				current_val = record[col.key];
			}
			html +=
				'<td class="ws-td-cell">' +
				me.get_editable_cell(col, row_key, String(current_val)) +
				"</td>";
		});

		// Save button
		var save_class = has_edits ? "btn-warning" : "btn-success";
		var save_disabled = has_edits ? "" : "disabled";
		html +=
			'<td class="ws-td-center"><button class="ws-save-row-btn ' +
			save_class +
			'" data-row-key="' +
			row_key +
			'" ' +
			save_disabled +
			">" +
			get_ws_icon("save", "12px") +
			"</button></td>";

		html += "</tr>";
		return html;
	},

	get_editable_cell: function (col, row_key, current_value) {
		var me = this;
		var name_attr = 'data-col="' + col.key + '" data-row-key="' + row_key + '"';
		var val = current_value || "";

		switch (col.type) {
			case "select":
				var opts = this.dropdown_options[col.options_key] || [];
				var h = '<select class="ws-cell ws-select" ' + name_attr + ">";
				h += '<option value=""></option>';
				opts.forEach(function (opt) {
					h +=
						'<option value="' +
						me.esc(opt) +
						'"' +
						(val === opt ? " selected" : "") +
						">" +
						me.esc(opt) +
						"</option>";
				});
				h += "</select>";
				return h;

			case "link":
				return (
					'<input type="text" class="ws-cell ws-link-cell" ' +
					name_attr +
					' value="' +
					me.esc(val) +
					'" placeholder="Search..." autocomplete="off" />'
				);

			case "date":
				var display_val = this.convert_iso_to_display(val);
				return (
					'<div class="ws-date-wrapper"><input type="text" class="ws-cell ws-date-cell" ' +
					name_attr +
					' value="' +
					me.esc(display_val) +
					'" placeholder="dd-mm-yyyy" autocomplete="off" />' +
					'<button class="btn btn-outline-secondary btn-sm ws-date-btn" data-col="' +
					col.key +
					'" data-row-key="' +
					row_key +
					'" title="Select date">' +
					get_ws_icon("calendar", "12px") +
					"</button></div>"
				);

			case "number":
				return (
					'<input type="number" class="ws-cell" ' +
					name_attr +
					' value="' +
					me.esc(val) +
					'" min="0" max="100" />'
				);

			case "currency":
			case "float":
				return (
					'<input type="number" class="ws-cell" ' +
					name_attr +
					' value="' +
					me.esc(val) +
					'" step="0.01" min="0" />'
				);

			default:
				return (
					'<input type="text" class="ws-cell" ' +
					name_attr +
					' value="' +
					me.esc(val) +
					'" autocomplete="off" />'
				);
		}
	},

	// -------------------------------------------------------------------------
	// TABLE EVENTS
	// -------------------------------------------------------------------------

	bind_table_events: function () {
		var me = this;
		var $c = this.$table_container;

		// Cell change
		$c.off("change input", ".ws-cell").on("change input", ".ws-cell", function () {
			var $el = $(this);
			var key = $el.data("row-key");
			var col = $el.data("col");
			if (!key || !col) return;
			if (!me.edited_rows[key]) me.edited_rows[key] = {};
			me.edited_rows[key][col] = $el.val();
			var $btn = $c.find('.ws-save-row-btn[data-row-key="' + key + '"]');
			me.set_save_btn_state($btn, "edited");
			me.update_save_all_count();
		});

		// Link cell click
		$c.off("click", ".ws-link-cell").on("click", ".ws-link-cell", function (e) {
			e.preventDefault();
			var $input = $(this);
			var col = $input.data("col");
			var col_def = me.editable_cols.find(function (c) {
				return c.key === col;
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
					if (val) $input.val(val).trigger("change");
					d.hide();
				},
			});
			d.show();
		});

		// Date button
		$c.off("click", ".ws-date-btn").on("click", ".ws-date-btn", function () {
			var $btn = $(this);
			var key = $btn.data("row-key");
			var col = $btn.data("col");
			var $input = $c.find(
				'.ws-date-cell[data-row-key="' + key + '"][data-col="' + col + '"]'
			);
			if (!$input.data("dp")) {
				var dp = $input
					.datepicker({
						language: "en",
						dateFormat: "dd-mm-yyyy",
						autoClose: true,
						onSelect: function () {
							$input.trigger("change");
						},
					})
					.data("datepicker");
				$input.data("dp", dp);
			}
			$input.data("dp").show();
		});

		// Save row
		$c.off("click", ".ws-save-row-btn").on("click", ".ws-save-row-btn", function () {
			var $btn = $(this);
			var key = $btn.data("row-key");
			me.save_row(key, $btn);
		});

		// ID link click
		$c.off("click", ".ws-id-link").on("click", ".ws-id-link", function (e) {
			e.preventDefault();
			var name = $(this).data("name");
			var doctype = $(this).data("doctype");
			if (name && doctype) frappe.set_route("Form", doctype, name);
		});

		// Select all
		$c.off("change", "#ws_select_all").on("change", "#ws_select_all", function () {
			$(".ws-select-checkbox").prop("checked", $(this).prop("checked"));
		});

		// Individual checkbox
		$c.off("change", ".ws-select-checkbox").on("change", ".ws-select-checkbox", function () {
			var total = $(".ws-select-checkbox").length;
			var checked = $(".ws-select-checkbox:checked").length;
			$("#ws_select_all").prop("checked", total === checked);
		});
	},

	// -------------------------------------------------------------------------
	// SAVE LOGIC
	// -------------------------------------------------------------------------

	save_row: function (row_key, $btn) {
		var me = this;
		this.set_save_btn_state($btn, "saving");
		$btn.html(get_ws_spinner("12px"));

		var row_data = this.build_row_data(row_key);

		// Always create new evaluation
		// Get record data for required fields
		var rec = this.records.find(function (r) {
			return r.name === row_key;
		});
		if (rec) {
			row_data.tea_lot = rec.name;
			row_data.invoice_number = rec.invoice_number || "";
			row_data.lot_no = rec.lot_no || "";
			row_data.mark = rec.mark || "";
		}

		frappe.call({
			method: this.API_BASE + ".create_evaluation",
			args: row_data,
			callback: function (r) {
				$btn.html(get_ws_icon("save", "12px"));
				if (r.message && r.message.success) {
					me.set_save_btn_state($btn, "saved");
					me.saved_rows[row_key] = true;
					delete me.edited_rows[row_key];
					me.update_save_all_count();
					var $row = me.$table_container.find('tr[data-row-key="' + row_key + '"]');
					$row.removeClass("row-edited");
					frappe.show_alert({
						message: __("Evaluation created."),
						indicator: "green",
					});
				} else {
					me.set_save_btn_state($btn, "error");
					frappe.msgprint(
						__("Error: {0}", [r.message ? r.message.message : "Unknown error"])
					);
				}
			},
			error: function () {
				$btn.html(get_ws_icon("save", "12px"));
				me.set_save_btn_state($btn, "error");
				frappe.msgprint(__("Error creating evaluation."));
			},
		});
	},

	build_row_data: function (row_key) {
		var row_data = {};
		var me = this;
		this.editable_keys.forEach(function (key) {
			var $cell = me.$table_container.find(
				'.ws-cell[data-row-key="' + row_key + '"][data-col="' + key + '"]'
			);
			var val = "";
			if ($cell.length) {
				val = $cell.val();
			} else if (me.edited_rows[row_key] && me.edited_rows[row_key][key] !== undefined) {
				val = me.edited_rows[row_key][key];
			}
			if (key === "evaluation_date" && val) {
				row_data[key] = me.convert_display_to_iso(val);
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
			frappe.show_alert({ message: __("No rows to save."), indicator: "orange" });
			return;
		}

		var $btn = this.$save_all_btn;
		$btn.prop("disabled", true).html(get_ws_spinner("16px") + " Saving...");

		var records_data = [];
		row_keys.forEach(function (key) {
			var row_data = me.build_row_data(key);
			var rec = me.records.find(function (r) {
				return r.name === key;
			});
			if (rec) {
				row_data.tea_lot = rec.name;
				row_data.invoice_number = rec.invoice_number || "";
				row_data.lot_no = rec.lot_no || "";
				row_data.mark = rec.mark || "";
			}
			records_data.push(row_data);
		});

		frappe.call({
			method: this.API_BASE + ".bulk_save",
			args: { records: JSON.stringify(records_data) },
			callback: function (r) {
				me.$save_all_btn
					.prop("disabled", false)
					.html(get_ws_icon("save_all", "16px") + " Save All");
				me.$save_all_count = $("#ws_save_all_count");
				me.update_save_all_count();

				if (r.message && r.message.results) {
					var failed = [];
					(r.message.results || []).forEach(function (res) {
						var key = res.tea_lot;
						var $sbtn = me.$table_container.find(
							'.ws-save-row-btn[data-row-key="' + key + '"]'
						);
						if (res.ok) {
							me.saved_rows[key] = true;
							delete me.edited_rows[key];
							if ($sbtn.length) {
								$sbtn.html(get_ws_icon("save", "12px"));
								me.set_save_btn_state($sbtn, "saved");
							}
							me.$table_container
								.find('tr[data-row-key="' + key + '"]')
								.removeClass("row-edited");
						} else {
							failed.push(me.esc(key) + ": " + me.esc(res.error));
							if ($sbtn.length) me.set_save_btn_state($sbtn, "error");
						}
					});
					me.update_save_all_count();
					frappe.show_alert({
						message: r.message.message,
						indicator: failed.length ? "orange" : "green",
					});
					if (failed.length) {
						frappe.msgprint({
							title: __("Some rows were not saved"),
							indicator: "red",
							message: failed.join("<br>"),
						});
					}
				} else {
					frappe.show_alert({
						message: r.message ? r.message.message : "Bulk save failed.",
						indicator: "red",
					});
				}
			},
			error: function () {
				me.$save_all_btn
					.prop("disabled", false)
					.html(get_ws_icon("save_all", "16px") + " Save All");
				me.update_save_all_count();
				frappe.show_alert({ message: __("Error saving records."), indicator: "red" });
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

	export_data: function () {
		var me = this;
		var $btn = $("#ws_export_btn");
		var orig = $btn.html();
		$btn.prop("disabled", true).html(get_ws_spinner("14px") + " Exporting...");

		this.collect_filters();

		// Collect only saved rows: use me.records for readonly data + me.edited_rows for editable data
		var table_data = [];
		var edited_keys = Object.keys(Object.assign({}, this.saved_rows, this.edited_rows));
		if (!edited_keys.length) {
			frappe.msgprint(__("Nothing to export. Edit or save some rows first."), "No Data");
			$btn.prop("disabled", false).html(orig);
			return;
		}

		edited_keys.forEach(function (row_key) {
			// Find the Tea Lot record for readonly fields
			var rec = me.records.find(function (r) {
				return r.name === row_key;
			});
			if (!rec) return;

			var vals = me.build_row_data(row_key);
			var row = {
				name: rec.name || "",
				lot_no: rec.lot_no || "",
				sale_no: rec.sale_no || "",
				mark: rec.mark || "",
				grade: rec.grade || "",
				invoice_number: rec.invoice_number || "",
				auction_centre: rec.auction_centre || "",
				taster: vals.taster || "",
				evaluation_stage: vals.evaluation_stage || "",
				liquor_mark: vals.liquor_mark || "",
				evaluation_date: vals.evaluation_date || "",
				suggested_valuation: vals.suggested_valuation || "",
				actual_valuation: vals.actual_valuation || "",
				colour: vals.colour || "",
				strength: vals.strength || "",
				taste: vals.taste || "",
				briskness: vals.briskness || "",
				quality_grade: vals.quality_grade || "",
				density: vals.density || "",
				remarks: vals.remarks || "",
			};

			table_data.push(row);
		});

		frappe.call({
			method: this.API_BASE + ".export_data",
			args: {
				filters: JSON.stringify(this.filter_values),
				table_data: JSON.stringify(table_data),
			},
			callback: function (r) {
				$btn.prop("disabled", false).html(orig);
				if (r.message && r.message.content) {
					try {
						var binary = atob(r.message.content);
						var bytes = new Uint8Array(binary.length);
						for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
						var blob = new Blob([bytes.buffer], {
							type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
						});
						var url = window.URL.createObjectURL(blob);
						var a = document.createElement("a");
						a.href = url;
						a.download = r.message.filename || "workspace_export.xlsx";
						document.body.appendChild(a);
						a.click();
						document.body.removeChild(a);
						window.URL.revokeObjectURL(url);
						frappe.show_alert({
							message: __("Exported successfully."),
							indicator: "green",
						});
					} catch (e) {
						console.error(e);
						frappe.msgprint(__("Error processing export."));
					}
				} else {
					frappe.msgprint(__("No data to export."));
				}
			},
			error: function () {
				$btn.prop("disabled", false).html(orig);
				frappe.msgprint(__("Export failed."));
			},
		});
	},

	// -------------------------------------------------------------------------
	// PAGINATION
	// -------------------------------------------------------------------------

	update_pagination: function () {
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
	// API CALL
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

	// -------------------------------------------------------------------------
	// SAVE BUTTON STATE
	// -------------------------------------------------------------------------

	set_save_btn_state: function ($btn, state) {
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
