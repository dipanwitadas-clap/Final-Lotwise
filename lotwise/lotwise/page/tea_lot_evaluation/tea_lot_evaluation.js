// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.pages["tea-lot-evaluation"].on_page_load = function (wrapper) {
	// ============================================================
	// PAGE SETUP
	// ============================================================

	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Tea Lot Evaluation"),
		single_column: true,
	});

	// ============================================================
	// STATE
	// ============================================================

	let all_lots = [];
	let dropdown_options = {
		stage: [],
		liquor_mark: [],
		quality_grade: [],
	};
	let edited_rows = {};
	let current_start = 0;
	let current_page_length = 20;
	let total_count = 0;
	let filter_values = {};
	let default_taster = "";
	let default_eval_date = "";
	let default_stage = "";

	// ============================================================
	// API HELPER
	// ============================================================

	function api(method, args, callback) {
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_evaluation.tea_lot_evaluation." + method,
			args: args,
			callback: function (r) {
				callback(r.message);
			},
			error: function (r) {
				console.error("API error:", method, r);
				callback(null);
			},
		});
	}

	// ============================================================
	// BUILD UI
	// ============================================================

	function build_page() {
		$(page.main).html(`
			<div class="tea-eval-page">
				<!-- FILTERS SECTION -->
				<div class="eval-card eval-card-filter">
					<div class="eval-card-header">
						<svg class="eval-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/></svg>
						<span>Filters</span>
					</div>
					<div class="eval-card-body">
						<div class="eval-filter-grid">
							<div class="eval-field">
								<label>Lot No</label>
								<input type="text" class="eval-filter" data-filter="lot_no" placeholder="Lot No" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Sale No</label>
								<input type="text" class="eval-filter" data-filter="sale_no" placeholder="Sale No" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Mark</label>
								<input type="text" class="eval-filter eval-link-filter-click" data-filter="mark" data-doctype="Mark" placeholder="Select Mark" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Grade</label>
								<input type="text" class="eval-filter eval-link-filter-click" data-filter="grade" data-doctype="Grade" placeholder="Select Grade" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Auction Centre</label>
								<input type="text" class="eval-filter eval-link-filter-click" data-filter="auction_centre" data-doctype="Auction Centre" placeholder="Select Auction Centre" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Status</label>
								<select class="eval-filter" data-filter="status">
									<option value="">All</option>
									<option value="Offered">Offered</option>
									<option value="Evaluated">Evaluated</option>
								</select>
							</div>
							<div class="eval-field eval-field-btn">
								<button class="eval-btn eval-btn-outline" id="clear_filters_btn">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
									Clear
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- DEFAULT VALUES SECTION -->
				<div class="eval-card eval-card-defaults">
					<div class="eval-card-header">
						<svg class="eval-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
						<span>Default Evaluation Values</span>
					</div>
					<div class="eval-card-body">
						<div class="eval-defaults-row">
							<div class="eval-field">
								<label>Taster</label>
								<input type="text" class="eval-default" id="default_taster" placeholder="Select Taster" autocomplete="off" />
							</div>
							<div class="eval-field">
								<label>Evaluation Date</label>
								<div class="eval-input-group">
									<input type="text" class="eval-default" id="default_eval_date" placeholder="dd/mm/yyyy" autocomplete="off" />
									<button class="eval-input-btn" id="default_eval_date_btn" title="Select date">
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
									</button>
								</div>
							</div>
							<div class="eval-field">
								<label>Stage</label>
								<select class="eval-default" id="default_stage">
									<option value=""></option>
								</select>
							</div>
							<div class="eval-field eval-field-btn">
								<button class="eval-btn eval-btn-save" id="save_all_btn">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
									Save All
									<span class="eval-badge" id="save_all_count">0</span>
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- TOOLBAR -->
				<div class="eval-toolbar">
					<div class="eval-toolbar-group">
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" id="bulk_update_taster_btn">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
							Taster
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="stage">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
							Stage
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="evaluation_date">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
							Eval Date
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="liquor_mark">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
							Liquor Mark
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="suggested_valuation">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
							Suggested Val
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="colour">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
							Colour
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="strength">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
							Strength
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="taste">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M12 20a8 8 0 100-16 8 8 0 000 16z"/><path d="M12 14a2 2 0 100-4 2 2 0 000 4z"/></svg>
							Taste
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="briskness">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
							Briskness
						</button>
						<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="quality_grade">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
							Quality Grade
						</button>
					<button class="eval-toolbar-btn eval-toolbar-btn-primary" data-field="density">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="9" y1="10" x2="15" y2="10"/><line x1="9" y1="14" x2="15" y2="14"/></svg>
						Density
					</button>
					<button class="eval-toolbar-btn eval-toolbar-btn-export" id="export_excel_btn">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
						Export Excel
					</button>
				</div>
				</div>

				<!-- TABLE CONTAINER -->
				<div class="eval-card eval-card-table">
					<div class="eval-card-body eval-card-body-table">
						<div class="eval-table-wrapper">
							<div id="eval_table_container">
								<div class="eval-loading">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:32px;height:32px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>
									<div>Loading Tea Lots...</div>
								</div>
							</div>
						</div>
					</div>
					<div class="eval-card-footer">
						<div class="eval-pagination">
							<div class="eval-pagination-info" id="pagination_info">No entries found</div>
							<div class="eval-pagination-controls">
								<div class="eval-page-size-group">
									<button class="eval-page-btn eval-page-size" data-value="20">20</button>
									<button class="eval-page-btn eval-page-size" data-value="100">100</button>
									<button class="eval-page-btn eval-page-size" data-value="500">500</button>
									<button class="eval-page-btn eval-page-size" data-value="2500">2500</button>
								</div>
								<div class="eval-nav-group">
									<button class="eval-page-btn" id="prev_page_btn" disabled>
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polyline points="15 18 9 12 15 6"/></svg>
									</button>
									<button class="eval-page-btn" id="next_page_btn">
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polyline points="9 18 15 12 9 6"/></svg>
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		// Add inner buttons in page header (next to search bar)
		page.add_inner_button(__("New Tea Lot"), function () {
			frappe.new_doc("Tea Lot");
		});

		page.add_inner_button(__("New Evaluation"), function () {
			frappe.new_doc("Tea Evaluation");
		});

		// Add styles
		add_styles();

		// Bind filter events
		bind_filter_events();

		// Bind default values events
		bind_default_events();

		// Bind toolbar events (Save All, Bulk Update, etc.)
		bind_toolbar_events();

		// Bind pagination events
		bind_pagination_events();

		// Bind export button event
		$("#export_excel_btn").on("click", function () {
			export_to_excel();
		});
	}

	// ============================================================
	// STYLES
	// ============================================================

	function add_styles() {
		$("<style>")
			.text(
				`
				@keyframes spin { to { transform: rotate(360deg); } }

				.tea-eval-page {
					padding: 0;
					font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
				}

				/* ===== CARDS ===== */
				.eval-card {
					background: #fff;
					border: 1px solid #e5e7eb;
					border-radius: 10px;
					margin-bottom: 12px;
					overflow: hidden;
					box-shadow: 0 1px 3px rgba(0,0,0,0.04);
				}
				.eval-card-header {
					display: flex;
					align-items: center;
					gap: 8px;
					padding: 10px 16px;
					font-size: 13px;
					font-weight: 600;
					color: #374151;
					background: #f9fafb;
					border-bottom: 1px solid #e5e7eb;
				}
				.eval-card-icon {
					width: 16px;
					height: 16px;
					color: #6b7280;
					flex-shrink: 0;
				}
				.eval-card-body {
					padding: 14px 16px;
				}
				.eval-card-body-table {
					padding: 0;
				}
				.eval-card-footer {
					padding: 10px 16px;
					border-top: 1px solid #e5e7eb;
					background: #f9fafb;
				}

				/* ===== FILTERS ===== */
				.eval-filter-grid {
					display: grid;
					grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
					gap: 10px;
					align-items: end;
				}
				.eval-field label {
					display: block;
					font-size: 11px;
					font-weight: 600;
					color: #6b7280;
					margin-bottom: 4px;
					text-transform: uppercase;
					letter-spacing: 0.3px;
				}
				.eval-field input,
				.eval-field select {
					width: 100%;
					height: 32px;
					padding: 0 10px;
					font-size: 13px;
					color: #374151;
					background: #fff;
					border: 1px solid #d1d5db;
					border-radius: 6px;
					outline: none;
					transition: border-color 0.15s, box-shadow 0.15s;
					box-sizing: border-box;
				}
				.eval-field input:focus,
				.eval-field select:focus {
					border-color: #3b82f6;
					box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
				}
				.eval-field input::placeholder {
					color: #9ca3af;
				}
				.eval-field-btn {
					display: flex;
					align-items: flex-end;
				}

				/* ===== DEFAULTS ===== */
				.eval-defaults-row {
					display: grid;
					grid-template-columns: 1fr 1fr 1fr auto;
					gap: 12px;
					align-items: end;
				}
				.eval-input-group {
					display: flex;
					gap: 0;
				}
				.eval-input-group input {
					border-radius: 6px 0 0 6px !important;
					border-right: none !important;
				}
				.eval-input-btn {
					display: flex;
					align-items: center;
					justify-content: center;
					width: 34px;
					height: 32px;
					border: 1px solid #d1d5db;
					border-radius: 0 6px 6px 0;
					background: #f9fafb;
					color: #6b7280;
					cursor: pointer;
					transition: background 0.15s;
				}
				.eval-input-btn:hover {
					background: #f3f4f6;
				}

				/* ===== BUTTONS ===== */
				.eval-btn {
					display: inline-flex;
					align-items: center;
					gap: 6px;
					height: 32px;
					padding: 0 14px;
					font-size: 13px;
					font-weight: 500;
					border: none;
					border-radius: 6px;
					cursor: pointer;
					transition: all 0.15s;
					white-space: nowrap;
				}
				.eval-btn-outline {
					background: #fff;
					color: #6b7280;
					border: 1px solid #d1d5db;
				}
				.eval-btn-outline:hover {
					background: #f3f4f6;
					border-color: #9ca3af;
				}
				.eval-btn-save {
					background: linear-gradient(135deg, #059669 0%, #047857 100%);
					color: #fff;
					font-weight: 600;
					box-shadow: 0 2px 4px rgba(5,150,105,0.2);
				}
				.eval-btn-save:hover {
					box-shadow: 0 4px 8px rgba(5,150,105,0.3);
					transform: translateY(-1px);
				}
				.eval-btn-save:disabled {
					opacity: 0.6;
					cursor: not-allowed;
					transform: none;
				}
				.eval-badge {
					display: inline-flex;
					align-items: center;
					justify-content: center;
					min-width: 20px;
					height: 20px;
					padding: 0 6px;
					font-size: 11px;
					font-weight: 700;
					color: #059669;
					background: rgba(255,255,255,0.9);
					border-radius: 10px;
				}

				/* ===== TOOLBAR ===== */
				.eval-toolbar {
					padding: 0 0 10px 0;
				}
				.eval-toolbar-group {
					display: flex;
					flex-wrap: wrap;
					gap: 6px;
				}
				.eval-toolbar-btn {
					display: inline-flex;
					align-items: center;
					gap: 5px;
					height: 30px;
					padding: 0 10px;
					font-size: 12px;
					font-weight: 500;
					color: #374151;
					background: #fff;
					border: 1px solid #d1d5db;
					border-radius: 6px;
					cursor: pointer;
					transition: all 0.15s;
					white-space: nowrap;
				}
				.eval-toolbar-btn:hover {
					background: #f3f4f6;
					border-color: #9ca3af;
				}
				.eval-toolbar-btn-primary {
					color: #fff;
					background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
					border-color: #3b82f6;
				}
				.eval-toolbar-btn-primary:hover {
					background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
					border-color: #2563eb;
				}
				.eval-toolbar-btn-export {
					color: #fff;
					background: linear-gradient(135deg, #10b981 0%, #059669 100%);
					border-color: #10b981;
					font-weight: 600;
				}
				.eval-toolbar-btn-export:hover {
					background: linear-gradient(135deg, #059669 0%, #047857 100%);
					border-color: #059669;
					box-shadow: 0 2px 4px rgba(16,185,129,0.3);
				}

				/* ===== TABLE ===== */
				.eval-table-wrapper {
					overflow: hidden;
				}
				#eval_table_container .table-responsive {
					max-height: calc(100vh - 360px);
					overflow-y: auto;
					overflow-x: auto;
				}
				#eval_table_container .table {
					margin-bottom: 0;
					white-space: nowrap;
					font-size: 12px;
					border-collapse: separate;
					border-spacing: 0;
					width: 100%;
				}
				#eval_table_container .table th {
					background: #f3f4f6;
					padding: 8px 8px;
					vertical-align: middle;
					border-bottom: 2px solid #e5e7eb;
					font-weight: 600;
					font-size: 11px;
					color: #4b5563;
					text-transform: uppercase;
					letter-spacing: 0.3px;
					position: sticky;
					top: 0;
					z-index: 1;
				}
				#eval_table_container .table td {
					padding: 5px 6px;
					vertical-align: middle;
					border-bottom: 1px solid #f3f4f6;
				}
				#eval_table_container .table tbody tr {
					transition: background 0.1s;
				}
				#eval_table_container .table tbody tr:hover {
					background: #f0f7ff;
				}
				#eval_table_container .table tbody tr:nth-child(even) {
					background: #fafbfc;
				}
				#eval_table_container .table tbody tr:nth-child(even):hover {
					background: #f0f7ff;
				}
				.eval-cell {
					height: 26px;
					font-size: 12px;
					padding: 2px 6px;
					border: 1px solid #d1d5db;
					border-radius: 4px;
					background: #fff;
					color: #374151;
					outline: none;
					transition: border-color 0.15s, box-shadow 0.15s;
					box-sizing: border-box;
				}
				.eval-cell:focus {
					border-color: #3b82f6 !important;
					box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
				}
				select.eval-cell {
					cursor: pointer;
				}
				.lot-id-link {
					color: #2563eb;
					font-weight: 600;
					text-decoration: none;
					cursor: pointer;
				}
				.lot-id-link:hover {
					text-decoration: underline;
					color: #1d4ed8;
				}
				.lot-select-checkbox {
					cursor: pointer;
					width: 15px;
					height: 15px;
					accent-color: #3b82f6;
				}
				.save-row-btn {
					padding: 3px 10px;
					font-size: 11px;
					border-radius: 4px;
					border: none;
					cursor: pointer;
					transition: all 0.15s;
					font-weight: 500;
				}
				.save-row-btn.btn-success {
					background: #d1fae5;
					color: #065f46;
				}
				.save-row-btn.btn-warning {
					background: #fef3c7;
					color: #92400e;
				}
				.save-row-btn.btn-danger {
					background: #fee2e2;
					color: #991b1b;
				}
				.save-row-btn:disabled {
					opacity: 0.5;
					cursor: not-allowed;
				}

				/* ===== PAGINATION ===== */
				.eval-pagination {
					display: flex;
					justify-content: space-between;
					align-items: center;
					gap: 12px;
				}
				.eval-pagination-info {
					font-size: 12px;
					color: #6b7280;
				}
				.eval-pagination-controls {
					display: flex;
					align-items: center;
					gap: 8px;
				}
				.eval-page-size-group {
					display: flex;
					border: 1px solid #d1d5db;
					border-radius: 6px;
					overflow: hidden;
				}
				.eval-page-btn {
					display: inline-flex;
					align-items: center;
					justify-content: center;
					height: 28px;
					padding: 0 10px;
					font-size: 12px;
					font-weight: 500;
					color: #374151;
					background: #fff;
					border: none;
					cursor: pointer;
					transition: all 0.1s;
				}
				.eval-page-btn:hover {
					background: #f3f4f6;
				}
				.eval-page-btn:disabled {
					opacity: 0.4;
					cursor: not-allowed;
				}
				.eval-page-size {
					border-right: 1px solid #d1d5db;
				}
				.eval-page-size:last-child {
					border-right: none;
				}
				.eval-page-size.active {
					background: #3b82f6;
					color: #fff;
				}
				.eval-nav-group {
					display: flex;
					border: 1px solid #d1d5db;
					border-radius: 6px;
					overflow: hidden;
				}
				.eval-nav-group .eval-page-btn {
					border-right: 1px solid #d1d5db;
				}
				.eval-nav-group .eval-page-btn:last-child {
					border-right: none;
				}

				/* ===== LOADING ===== */
				.eval-loading {
					display: flex;
					flex-direction: column;
					align-items: center;
					gap: 8px;
					padding: 40px;
					color: #9ca3af;
					font-size: 13px;
				}

				/* ===== RESPONSIVE ===== */
				@media (max-width: 768px) {
					.eval-filter-grid {
						grid-template-columns: 1fr 1fr;
					}
					.eval-defaults-row {
						grid-template-columns: 1fr;
					}
					.eval-pagination {
						flex-direction: column;
						gap: 8px;
					}
				}
			`
			)
			.appendTo("head");
	}

	// ============================================================
	// FILTER EVENTS
	// ============================================================

	function bind_filter_events() {
		// Filter on any change/input immediately
		$(".eval-filter").on("change input", function () {
			collect_filters();
			current_start = 0;
			load_data();
		});

		$("#clear_filters_btn").on("click", function () {
			$(".eval-filter").val("");
			filter_values = {};
			current_start = 0;
			load_data();
		});

		// Link filter click - open Link selector (Mark, Grade, Auction Centre)
		$(".eval-link-filter-click").on("click", function () {
			var $input = $(this);
			var doctype = $input.data("doctype");

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
	}

	function collect_filters() {
		filter_values = {};
		$(".eval-filter").each(function () {
			var $el = $(this);
			var key = $el.data("filter");
			var val = $el.val();
			if (val && String(val).trim() !== "") {
				filter_values[key] = val.trim();
			}
		});
	}

	// ============================================================
	// DEFAULT VALUES EVENTS
	// ============================================================

	function bind_default_events() {
		// Taster default - click to open Link selector
		$("#default_taster").on("click", function () {
			var $input = $(this);
			var d = new frappe.ui.Dialog({
				title: __("Select Taster"),
				fields: [
					{
						fieldname: "link_field",
						label: "Taster",
						fieldtype: "Link",
						options: "Taster",
					},
				],
				primary_action_label: __("Select"),
				primary_action: function () {
					var val = d.get_values().link_field;
					if (val) {
						$input.val(val);
						default_taster = val;
						// Force apply to ALL rows (overwrites manual edits)
						apply_default_taster_to_all();
						// Enable save buttons for rows with default applied
						enable_save_buttons_for_defaults();
					}
					d.hide();
				},
			});
			d.show();
		});

		// Also apply on manual typing - force apply to ALL rows
		$("#default_taster").on("change input", function () {
			default_taster = $(this).val();
			apply_default_taster_to_all();
			enable_save_buttons_for_defaults();
		});

		// Evaluation Date default - auto-populate on change
		$("#default_eval_date").on("change input", function () {
			default_eval_date = $(this).val();
			apply_defaults_to_table();
		});

		// Stage default - auto-populate on change
		$("#default_stage").on("change", function () {
			default_stage = $(this).val();
			apply_defaults_to_table();
		});

		// Evaluation Date picker button
		$("#default_eval_date_btn").on("click", function () {
			var $input = $("#default_eval_date");
			if (!$input.data("dp")) {
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
			}
			$input.data("dp").show();
		});
	}

	function apply_default_taster_to_all() {
		// Force apply default taster to ALL rows (overwrites manual edits too)
		// Called only when user explicitly changes the default taster field
		var $container = $("#eval_table_container");
		$container.find('.eval-cell[data-col="taster"]').each(function () {
			var $cell = $(this);
			$cell.val(default_taster);
			var row_key = $cell.data("row-key");
			if (row_key) {
				if (!edited_rows[row_key]) edited_rows[row_key] = {};
				edited_rows[row_key]["taster"] = default_taster;
			}
		});
	}

	function apply_defaults_to_table() {
		var $container = $("#eval_table_container");

		// Apply taster to rows without manual taster edits
		if (default_taster) {
			$container.find('.eval-cell[data-col="taster"]').each(function () {
				var $cell = $(this);
				var row_key = $cell.data("row-key");
				// Skip rows that were manually edited (e.g. via bulk update)
				if (
					row_key &&
					edited_rows[row_key] &&
					edited_rows[row_key]["taster"] !== undefined
				) {
					return;
				}
				$cell.val(default_taster);
				if (row_key) {
					if (!edited_rows[row_key]) edited_rows[row_key] = {};
					edited_rows[row_key]["taster"] = default_taster;
				}
			});
		}

		// Apply evaluation date to rows without manual eval_date edits
		if (default_eval_date) {
			$container.find('.eval-cell[data-col="evaluation_date"]').each(function () {
				var $cell = $(this);
				var row_key = $cell.data("row-key");
				// Skip rows that were manually edited
				if (
					row_key &&
					edited_rows[row_key] &&
					edited_rows[row_key]["evaluation_date"] !== undefined
				) {
					return;
				}
				$cell.val(default_eval_date);
				if (row_key) {
					if (!edited_rows[row_key]) edited_rows[row_key] = {};
					edited_rows[row_key]["evaluation_date"] = default_eval_date;
				}
			});
		}

		// Apply stage to all rows (always - even blank to clear)
		$container.find('.eval-cell[data-col="stage"]').each(function () {
			var $cell = $(this);
			$cell.val(default_stage);
			var row_key = $cell.data("row-key");
			if (row_key) {
				if (!edited_rows[row_key]) edited_rows[row_key] = {};
				edited_rows[row_key]["stage"] = default_stage;
			}
		});

		// Enable save buttons for rows that got defaults applied
		if (default_taster || default_eval_date) {
			$container.find(".save-row-btn").each(function () {
				var $btn = $(this);
				var row_key = $btn.data("row-key");
				if (
					row_key &&
					edited_rows[row_key] &&
					Object.keys(edited_rows[row_key]).length > 0
				) {
					$btn.prop("disabled", false)
						.removeClass("btn-success")
						.addClass("btn-warning");
				}
			});
		}
	}

	function enable_save_buttons_for_defaults() {
		var $container = $("#eval_table_container");
		$container.find(".save-row-btn").each(function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			if (row_key && edited_rows[row_key] && Object.keys(edited_rows[row_key]).length > 0) {
				$btn.prop("disabled", false).removeClass("btn-success").addClass("btn-warning");
			}
		});
		update_save_all_count();
	}

	function update_save_all_count() {
		var count = Object.keys(edited_rows).length;
		var $badge = $("#save_all_count");
		if (count > 0) {
			$badge.text(count).show();
		} else {
			$badge.hide();
		}
	}

	// ============================================================
	// TOOLBAR EVENTS
	// ============================================================

	function bind_toolbar_events() {
		$("#save_all_btn").on("click", function () {
			save_all_rows();
		});

		// Bulk update taster for selected rows
		$("#bulk_update_taster_btn").on("click", function () {
			var $checked = $(".lot-select-checkbox:checked");
			if (!$checked.length) {
				frappe.msgprint(__("Please select at least one row to update."));
				return;
			}

			var d = new frappe.ui.Dialog({
				title: __("Update Taster"),
				fields: [
					{
						fieldname: "taster",
						label: "Taster",
						fieldtype: "Link",
						options: "Taster",
					},
				],
				primary_action_label: __("Update"),
				primary_action: function () {
					var val = d.get_values().taster;
					if (!val) {
						frappe.msgprint(__("Please select a Taster."));
						return;
					}

					var updated_count = 0;
					$checked.each(function () {
						var row_key = $(this).data("row-key");
						if (!row_key) return;
						var $cell = $("#eval_table_container").find(
							'.eval-cell[data-row-key="' + row_key + '"][data-col="taster"]'
						);
						if ($cell.length) {
							$cell.val(val);
							if (!edited_rows[row_key]) edited_rows[row_key] = {};
							edited_rows[row_key]["taster"] = val;
							// Enable save button
							var $save_btn = $("#eval_table_container").find(
								'.save-row-btn[data-row-key="' + row_key + '"]'
							);
							$save_btn
								.prop("disabled", false)
								.removeClass("btn-success")
								.addClass("btn-warning");
							updated_count++;
						}
					});

					frappe.show_alert({
						message: __("Taster updated for {0} row(s).", [updated_count]),
						indicator: "green",
					});
					d.hide();
				},
			});
			d.show();
		});

		// Bulk update buttons for other fields (only those with data-field attribute)
		$(".eval-toolbar-btn-primary").on("click", function () {
			var field = $(this).data("field");
			if (field) {
				bulk_update_field(field);
			}
		});
	}

	// ============================================================
	// BULK UPDATE FIELD (for selected rows)
	// ============================================================

	function bulk_update_field(field) {
		var $checked = $(".lot-select-checkbox:checked");
		if (!$checked.length) {
			frappe.msgprint(__("Please select at least one row to update."));
			return;
		}

		// Determine field config
		var field_config = get_field_config(field);
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

				var updated_count = 0;
				$checked.each(function () {
					var row_key = $(this).data("row-key");
					if (!row_key) return;
					var $cell = $("#eval_table_container").find(
						'.eval-cell[data-row-key="' + row_key + '"][data-col="' + field + '"]'
					);
					if ($cell.length) {
						$cell.val(val);
						if (!edited_rows[row_key]) edited_rows[row_key] = {};
						edited_rows[row_key][field] = val;
						// Enable save button
						var $save_btn = $("#eval_table_container").find(
							'.save-row-btn[data-row-key="' + row_key + '"]'
						);
						$save_btn
							.prop("disabled", false)
							.removeClass("btn-success")
							.addClass("btn-warning");
						updated_count++;
					}
				});

				frappe.show_alert({
					message: __("{0} updated for {1} row(s).", [
						field_config.label,
						updated_count,
					]),
					indicator: "green",
				});
				d.hide();
			},
		});
		d.show();
	}

	function get_field_config(field) {
		var config_map = {
			stage: {
				label: "Stage",
				fieldtype: "Select",
				options: dropdown_options.stage ? dropdown_options.stage.join("\n") : "",
			},
			evaluation_date: {
				label: "Eval Date",
				fieldtype: "Date",
				options: null,
			},
			liquor_mark: {
				label: "Liquor Mark",
				fieldtype: "Select",
				options: dropdown_options.liquor_mark
					? dropdown_options.liquor_mark.join("\n")
					: "",
			},
			suggested_valuation: {
				label: "Suggested Val",
				fieldtype: "Float",
				options: null,
			},
			colour: {
				label: "Colour",
				fieldtype: "Int",
				options: null,
			},
			strength: {
				label: "Strength",
				fieldtype: "Int",
				options: null,
			},
			taste: {
				label: "Taste",
				fieldtype: "Int",
				options: null,
			},
			briskness: {
				label: "Briskness",
				fieldtype: "Int",
				options: null,
			},
			quality_grade: {
				label: "Quality Grade",
				fieldtype: "Select",
				options: dropdown_options.quality_grade
					? dropdown_options.quality_grade.join("\n")
					: "",
			},
			density: {
				label: "Density",
				fieldtype: "Float",
				options: null,
			},
		};
		return config_map[field] || null;
	}

	// ============================================================
	// PAGINATION EVENTS
	// ============================================================

	function bind_pagination_events() {
		$(".eval-page-size").on("click", function () {
			var $this = $(this);
			var new_page_length = parseInt($this.data("value"));

			$(".eval-page-size").removeClass("active");
			$this.addClass("active");

			current_page_length = new_page_length;
			current_start = 0;
			load_data();
		});

		// Set default active page size
		$('.eval-page-size[data-value="20"]').addClass("active");

		$("#prev_page_btn").on("click", function () {
			if (current_start > 0) {
				current_start = Math.max(0, current_start - current_page_length);
				load_data();
			}
		});

		$("#next_page_btn").on("click", function () {
			if (current_start + current_page_length < total_count) {
				current_start = current_start + current_page_length;
				load_data();
			}
		});
	}

	function update_pagination_ui() {
		var end = Math.min(current_start + current_page_length, total_count);
		if (total_count > 0) {
			$("#pagination_info").html(
				"Showing " + (current_start + 1) + " to " + end + " of " + total_count + " entries"
			);
		} else {
			$("#pagination_info").html("No entries found");
		}
		$("#prev_page_btn").prop("disabled", current_start === 0);
		$("#next_page_btn").prop("disabled", end >= total_count);
	}

	// ============================================================
	// LOAD DATA
	// ============================================================

	function load_data() {
		$("#eval_table_container").html(
			'<div class="eval-loading">' +
				'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:32px;height:32px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>' +
				"<div>Loading Tea Lots...</div>" +
				"</div>"
		);

		api(
			"get_evaluation_lots",
			{
				filters: JSON.stringify(filter_values),
				start: current_start,
				page_length: current_page_length,
			},
			function (result) {
				if (result) {
					all_lots = result.lots || [];
					total_count = result.total_count || 0;

					// Remove edited_rows for rows that are no longer in the current filtered set
					var current_names = new Set(
						all_lots.map(function (l) {
							return l.name;
						})
					);
					Object.keys(edited_rows).forEach(function (key) {
						if (!current_names.has(key)) {
							delete edited_rows[key];
						}
					});
					update_save_all_count();
					dropdown_options = {
						stage: result.stage_options || [],
						liquor_mark: result.liquor_mark_options || [],
						quality_grade: result.quality_grade_options || [],
					};

					// Populate default stage dropdown
					var $stage = $("#default_stage");
					$stage.empty();
					$stage.append('<option value=""></option>');
					(result.stage_options || []).forEach(function (opt) {
						$stage.append('<option value="' + opt + '">' + opt + "</option>");
					});
					// Preserve previously selected default stage
					if (default_stage) {
						$stage.val(default_stage);
					}

					render_table();
					update_pagination_ui();

					// Apply defaults after table renders
					apply_defaults_to_table();
				} else {
					$("#eval_table_container").html(
						'<div class="alert alert-info m-3">No data available.</div>'
					);
				}
			}
		);
	}

	// ============================================================
	// COLUMN DEFINITIONS
	// ============================================================

	var readonly_cols = [
		{ key: "idx", label: "#", width: 35 },
		{ key: "name", label: "ID", width: 140, clickable: true },
		{ key: "sale_no", label: "Sale No", width: 80 },
		{ key: "lot_no", label: "Lot No", width: 80 },
		{ key: "auction_centre", label: "Action Centre", width: 100 },
		{ key: "grade", label: "Grade", width: 80 },
		{ key: "invoice_number", label: "Invoice No", width: 100 },
		{ key: "mark", label: "Mark", width: 80 },
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

	// ============================================================
	// RENDER TABLE (Manual HTML - no DataTable)
	// ============================================================

	function render_table() {
		if (!all_lots.length) {
			$("#eval_table_container").html(
				'<div class="alert alert-info m-3">No Tea Lots found.</div>'
			);
			return;
		}

		var html = '<div class="table-responsive">';
		html += '<table class="table" id="eval_table">';
		html += "<thead><tr>";

		// Checkbox header
		html +=
			'<th style="width:36px;text-align:center;vertical-align:middle;">' +
			'<input type="checkbox" id="select_all_lots" title="Select All" style="cursor:pointer;width:15px;height:15px;accent-color:#3b82f6;" /></th>';

		// Readonly column headers
		readonly_cols.forEach(function (col) {
			html +=
				'<th style="min-width:' +
				col.width +
				'px;">' +
				frappe.utils.escape_html(col.label) +
				"</th>";
		});

		// Editable column headers
		editable_cols.forEach(function (col) {
			html +=
				'<th style="min-width:' +
				col.width +
				'px;">' +
				frappe.utils.escape_html(col.label) +
				"</th>";
		});

		// Save column header
		html += '<th style="min-width:50px;text-align:center;">Save</th>';

		html += "</tr></thead><tbody>";

		all_lots.forEach(function (lot, idx) {
			var row_key = lot.name;
			var has_edits = edited_rows[row_key] ? true : false;

			html += '<tr data-row-key="' + row_key + '" data-idx="' + idx + '">';

			// Checkbox cell
			html +=
				'<td style="text-align:center;vertical-align:middle;padding:4px;">' +
				'<input type="checkbox" class="lot-select-checkbox" data-row-key="' +
				row_key +
				'" /></td>';

			// Readonly cells
			readonly_cols.forEach(function (col) {
				var val = col.key === "idx" ? current_start + idx + 1 : lot[col.key] || "";
				if (col.clickable) {
					html +=
						'<td style="padding:6px 8px;">' +
						'<a href="#" class="lot-id-link" data-lot-name="' +
						frappe.utils.escape_html(val) +
						'">' +
						frappe.utils.escape_html(String(val)) +
						"</a></td>";
				} else {
					html +=
						'<td style="padding:6px 8px;">' +
						frappe.utils.escape_html(String(val)) +
						"</td>";
				}
			});

			// Editable cells
			editable_cols.forEach(function (col) {
				html += '<td style="padding:3px 4px;">';

				// Use edited value if available, otherwise use original
				var current_val = "";
				if (edited_rows[row_key] && edited_rows[row_key][col.key] !== undefined) {
					current_val = edited_rows[row_key][col.key];
				} else if (lot[col.key] !== undefined && lot[col.key] !== null) {
					current_val = lot[col.key];
				}

				html += get_editable_cell_html(col, row_key, String(current_val));
				html += "</td>";
			});

			// Save button cell
			var save_disabled = has_edits ? "" : "disabled";
			var save_class = has_edits ? "btn-warning" : "btn-success";
			html +=
				'<td style="text-align:center;padding:3px 4px;">' +
				'<button class="save-row-btn ' +
				save_class +
				'" data-row-key="' +
				row_key +
				'" ' +
				save_disabled +
				">" +
				'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg></button></td>';

			html += "</tr>";
		});

		html += "</tbody></table></div>";

		$("#eval_table_container").html(html);

		// Bind all events
		bind_table_events();
	}

	// ============================================================
	// GENERATE EDITABLE CELL HTML
	// ============================================================

	function get_editable_cell_html(col, row_key, current_value) {
		var name_attr = 'data-col="' + col.key + '" data-row-key="' + row_key + '"';
		var val = current_value || "";

		switch (col.type) {
			case "select":
				var opts = dropdown_options[col.options_key] || [];
				var h = '<select class="eval-cell" ' + name_attr + ' style="min-width:60px;">';
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
					'"' +
					' style="min-width:60px;" placeholder="Search..." autocomplete="off" />'
				);

			case "date":
				return (
					'<div style="display:flex;gap:0;">' +
					'<input type="text" class="eval-cell eval-date" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'"' +
					' placeholder="dd/mm/yyyy"' +
					' style="min-width:60px;border-radius:4px 0 0 4px;" autocomplete="off" />' +
					'<button class="eval-date-btn" ' +
					'data-col="' +
					col.key +
					'" data-row-key="' +
					row_key +
					'" ' +
					'style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border:1px solid #d1d5db;border-left:none;border-radius:0 4px 4px 0;background:#f9fafb;color:#6b7280;cursor:pointer;padding:0;" title="Select date">' +
					'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></button></div>'
				);

			case "number":
				return (
					'<input type="number" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'"' +
					' min="0" max="100"' +
					' style="min-width:50px;" />'
				);

			case "currency":
				return (
					'<input type="number" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'"' +
					' step="0.01" min="0"' +
					' style="min-width:60px;" />'
				);

			case "float":
				return (
					'<input type="number" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'"' +
					' step="0.01" min="0"' +
					' style="min-width:60px;" />'
				);

			default:
				return (
					'<input type="text" class="eval-cell" ' +
					name_attr +
					' value="' +
					frappe.utils.escape_html(val) +
					'"' +
					' style="min-width:60px;" autocomplete="off" />'
				);
		}
	}

	// ============================================================
	// BIND TABLE EVENTS (uses jQuery delegation on container)
	// ============================================================

	function bind_table_events() {
		var $container = $("#eval_table_container");

		// Edit cell change
		$container.off("change input", ".eval-cell").on("change input", ".eval-cell", function () {
			var $el = $(this);
			var row_key = $el.data("row-key");
			var col_key = $el.data("col");

			if (!row_key || !col_key) return;

			if (!edited_rows[row_key]) {
				edited_rows[row_key] = {};
			}
			edited_rows[row_key][col_key] = $el.val();

			// Enable save button, make it warning
			var $save_btn = $container.find('.save-row-btn[data-row-key="' + row_key + '"]');
			$save_btn.prop("disabled", false);
			$save_btn.removeClass("btn-success").addClass("btn-warning");
			update_save_all_count();
		});

		// Link cell click - open selector dialog
		$container.off("click", ".eval-link").on("click", ".eval-link", function () {
			var $input = $(this);
			// Get doctype from column definition
			var col_key = $input.data("col");
			var col_def = null;
			for (var i = 0; i < editable_cols.length; i++) {
				if (editable_cols[i].key === col_key) {
					col_def = editable_cols[i];
					break;
				}
			}
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
		$container.off("click", ".eval-date-btn").on("click", ".eval-date-btn", function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			var col = $btn.data("col");
			var $input = $container.find(
				'.eval-date[data-row-key="' + row_key + '"][data-col="' + col + '"]'
			);

			if (!$input.data("dp")) {
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
			}
			$input.data("dp").show();
		});

		// Save row button click
		$container.off("click", ".save-row-btn").on("click", ".save-row-btn", function () {
			var $btn = $(this);
			var row_key = $btn.data("row-key");
			save_row(row_key, $btn);
		});

		// ID link click
		$container.off("click", ".lot-id-link").on("click", ".lot-id-link", function (e) {
			e.preventDefault();
			var lot_name = $(this).data("lot-name");
			if (lot_name) {
				frappe.set_route("Form", "Tea Lot", lot_name);
			}
		});

		// Select all checkbox
		$container.off("change", "#select_all_lots").on("change", "#select_all_lots", function () {
			var checked = $(this).prop("checked");
			$(".lot-select-checkbox").prop("checked", checked);
		});

		// Individual checkbox
		$container
			.off("change", ".lot-select-checkbox")
			.on("change", ".lot-select-checkbox", function () {
				var total = $(".lot-select-checkbox").length;
				var checked = $(".lot-select-checkbox:checked").length;
				$("#select_all_lots").prop("checked", total === checked);
			});
	}

	// ============================================================
	// SAVE LOGIC
	// ============================================================

	function save_row(row_key, $btn) {
		$btn.prop("disabled", true).html(
			'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>'
		);

		var row_data = build_row_data(row_key);

		if (!row_data.taster || !row_data.stage || !row_data.evaluation_date) {
			frappe.msgprint(
				__("Row {0}: Taster, Stage, and Evaluation Date are required.", [row_key])
			);
			$btn.prop("disabled", false).html(
				'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg>'
			);
			return;
		}

		frappe.call({
			method: "lotwise.lotwise.doctype.tea_lot.tea_lot.create_tea_evaluation",
			args: row_data,
			callback: function (r) {
				if (r.message) {
					$btn.html(
						'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg>'
					);
					$btn.removeClass("btn-warning btn-danger").addClass("btn-success");
					$btn.prop("disabled", true);
					delete edited_rows[row_key];
					frappe.show_alert({
						message: __("Evaluation created for {0}", [row_key]),
						indicator: "green",
					});
				} else {
					$btn.prop("disabled", false).html(
						'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg>'
					);
					$btn.addClass("btn-danger").removeClass("btn-warning btn-success");
				}
			},
			error: function () {
				$btn.prop("disabled", false).html(
					'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg>'
				);
				$btn.addClass("btn-danger").removeClass("btn-warning btn-success");
			},
		});
	}

	function build_row_data(row_key) {
		var lot = all_lots.find(function (d) {
			return d.name === row_key;
		});
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
			"density",
			"remarks",
		];

		// Read values directly from the DOM
		var $container = $("#eval_table_container");
		editable_keys.forEach(function (key) {
			var $cell = $container.find(
				'.eval-cell[data-row-key="' + row_key + '"][data-col="' + key + '"]'
			);
			var val = "";
			if ($cell.length) {
				val = $cell.val();
			} else if (edited_rows[row_key] && edited_rows[row_key][key] !== undefined) {
				val = edited_rows[row_key][key];
			}

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
		});

		// Add Tea Lot fields needed for evaluation
		if (lot) {
			row_data.invoice_number = lot.invoice_number || "";
			row_data.mark = lot.mark || "";
		}

		return row_data;
	}

	function save_all_rows() {
		// Collect all row keys that have ANY edited values
		var row_keys = Object.keys(edited_rows);
		if (!row_keys.length) {
			frappe.show_alert({
				message: __("No rows to save. Edit some fields first."),
				indicator: "orange",
			});
			return;
		}

		var $btn = $("#save_all_btn");
		$btn.prop("disabled", true).html(
			'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg> Saving...'
		);

		var saved_count = 0;
		var total = row_keys.length;
		var completed = 0;

		row_keys.forEach(function (row_key) {
			var row_data = build_row_data(row_key);

			if (!row_data.taster || !row_data.stage || !row_data.evaluation_date) {
				completed++;
				if (completed === total) {
					finish_save_all($btn, saved_count, total);
				}
				return;
			}

			frappe.call({
				method: "lotwise.lotwise.doctype.tea_lot.tea_lot.create_tea_evaluation",
				args: row_data,
				callback: function (r) {
					completed++;
					if (r.message) {
						saved_count++;
						delete edited_rows[row_key];
						// Update the save button in the DOM
						var $save_btn = $("#eval_table_container").find(
							'.save-row-btn[data-row-key="' + row_key + '"]'
						);
						if ($save_btn.length) {
							$save_btn
								.html(
									'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"/></svg>'
								)
								.prop("disabled", true)
								.removeClass("btn-warning btn-danger")
								.addClass("btn-success");
						}
					}
					if (completed === total) {
						finish_save_all($btn, saved_count, total);
					}
				},
				error: function () {
					completed++;
					if (completed === total) {
						finish_save_all($btn, saved_count, total);
					}
				},
			});
		});
	}

	function finish_save_all($btn, saved_count, total) {
		$btn.prop("disabled", false).html(
			'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save All' +
				'<span class="eval-badge" id="save_all_count">' +
				Object.keys(edited_rows).length +
				"</span>"
		);
		update_save_all_count();
		frappe.show_alert({
			message: saved_count + " of " + total + " evaluation(s) created successfully.",
			indicator: saved_count > 0 ? "green" : "orange",
		});
	}

	// ============================================================
	// EXPORT FUNCTIONALITY
	// ============================================================

	function export_to_excel() {
		// Show loading message
		var original_text = $("#export_excel_btn").html();
		$("#export_excel_btn")
			.prop("disabled", true)
			.html(
				'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;animation:spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg> Exporting...'
			);

		// Collect current filters
		collect_filters();

		// Call backend API
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_evaluation.tea_lot_evaluation.export_evaluation_lots",
			args: {
				filters: JSON.stringify(filter_values),
			},
			callback: function (r) {
				// Reset button
				$("#export_excel_btn").prop("disabled", false).html(original_text);

				if (r.message && r.message.content) {
					try {
						// Decode base64 content
						var base64Content = r.message.content;
						var binaryString = atob(base64Content);
						var bytes = new Uint8Array(binaryString.length);
						for (var i = 0; i < binaryString.length; i++) {
							bytes[i] = binaryString.charCodeAt(i);
						}

						// Create blob and download
						var blob = new Blob([bytes.buffer], {
							type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
						});
						var url = window.URL.createObjectURL(blob);
						var a = document.createElement("a");
						a.href = url;
						a.download = r.message.filename || "tea_lot_evaluation.xlsx";
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
				// Reset button
				$("#export_excel_btn").prop("disabled", false).html(original_text);
				frappe.msgprint(__("Error exporting data. Please try again."));
				console.error("Export error:", r);
			},
		});
	}

	// ============================================================
	// INIT
	// ============================================================

	function init_page() {
		build_page();
		load_data();
	}

	// Start the page
	init_page();
};
