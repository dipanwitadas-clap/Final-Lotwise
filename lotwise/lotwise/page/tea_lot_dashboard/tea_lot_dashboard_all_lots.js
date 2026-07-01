// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

/* global lotwise */

// ============================================================
// All Tea Lots - Filterable Table & Detail Modal
// ============================================================

frappe.provide("lotwise.tea_lot_dashboard");

(function () {
	"use strict";

	var all_lots_data = [];
	var filter_timeout = null;
	var current_page = 0;
	var page_size = 10;

	// Shared helpers from main page (must be available in scope)
	function api(method, args, callback) {
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_dashboard." + method,
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

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function money(value) {
		return "₹ " + lotwise_format(value);
	}

	function value_or_dash(value) {
		return value == null || value === "" ? "-" : esc(value);
	}

	function lotwise_format(value) {
		return Number(value || 0).toLocaleString("en-IN", {
			maximumFractionDigits: 2,
		});
	}

	// ============================================================
	// LOAD ALL LOTS
	// ============================================================

	var flt_from_date_field = null;
	var flt_to_date_field = null;

	function get_date_filter_args() {
		var args = {};
		var from_date = flt_from_date_field ? flt_from_date_field.get_value() : "";
		var to_date = flt_to_date_field ? flt_to_date_field.get_value() : "";
		if (from_date) args.from_date = from_date;
		if (to_date) args.to_date = to_date;
		return args;
	}

	function create_date_filter_controls() {
		if (flt_from_date_field) return; // already created

		flt_from_date_field = frappe.ui.form.make_control({
			parent: $("#flt_from_date_wrapper"),
			df: {
				fieldname: "flt_from_date",
				fieldtype: "Date",
				label: "From Purchase Date",
				placeholder: "dd/mm/yyyy",
				onchange: function () {
					load_all_lots();
				},
			},
			render_input: true,
		});
		flt_from_date_field.refresh();

		flt_to_date_field = frappe.ui.form.make_control({
			parent: $("#flt_to_date_wrapper"),
			df: {
				fieldname: "flt_to_date",
				fieldtype: "Date",
				label: "To Purchase Date",
				placeholder: "dd/mm/yyyy",
				onchange: function () {
					load_all_lots();
				},
			},
			render_input: true,
		});
		flt_to_date_field.refresh();
	}

	function load_all_lots() {
		// Build the wrapper with persistent heading row (only once)
		if (!$("#tea_lot_all").length) return;
		if (!$("#tea_lot_all_heading").length) {
			$("#tea_lot_all").html(`
				<div class="detail-box">
					<div class="section-heading" id="tea_lot_all_heading">
						<div class="section-title-wrap">
							<h4>All Tea Lots</h4>
							<span class="lot-count-badge" id="total_lot_count">0 Total</span>
							<span class="lot-badge" id="filtered_lot_count" style="background:#fef3c7;color:#92400e;display:none;">0 Filtered</span>
							<div id="flt_from_date_wrapper" style="display:inline-block;width:160px;"></div>
							<span style="font-size:12px;color:#6b7280;">to</span>
							<div id="flt_to_date_wrapper" style="display:inline-block;width:160px;"></div>
						</div>
					</div>
					<div id="tea_lot_all_container"></div>
				</div>
			`);
			create_date_filter_controls();
		}

		$("#tea_lot_all_container").html(`
			<div class="text-center text-muted" style="padding:20px;">
				<i class="fa fa-spinner fa-spin"></i>
				Loading all tea lots...
			</div>
		`);

		var args = get_date_filter_args();
		api("tea_lot_dashboard_all_lots.get_all_lots", args, function (data) {
			all_lots_data = (data && data.lots) || [];
			render_all_lots_table();
		});
	}

	// ============================================================
	// RENDER FILTERABLE TABLE
	// ============================================================

	function render_all_lots_table() {
		// Save focus state before re-render so the user can keep typing
		var focused_filter_id = null;
		var cursor_start = 0;
		var cursor_end = 0;
		var active = document.activeElement;
		if (active && active.id && active.id.indexOf("flt_") === 0) {
			focused_filter_id = active.id;
			cursor_start = active.selectionStart || 0;
			cursor_end = active.selectionEnd || 0;
		}

		var data = all_lots_data;

		if (!data.length) {
			$("#tea_lot_all_container").html(`
				<div class="detail-box text-center text-muted">
					No Tea Lots found.
				</div>
			`);
			return;
		}

		var columns = [
			{ key: "sno", label: "S.No" },
			{ key: "name", label: "Tea Lot ID", clickable: true },
			{ key: "lot_no", label: "Lot No" },
			{ key: "mark", label: "Mark" },
			{ key: "grade", label: "Grade" },
			{ key: "seller", label: "Seller" },
			{ key: "invoice_number", label: "Invoice No" },
			{ key: "liquor_mark", label: "Liquor Mark" },
			{ key: "acquisition_channel", label: "Channel" },
			{ key: "purchase_date", label: "Purchase Date" },
			{ key: "packages", label: "Packages", numeric: true },
			{ key: "net_weight_total", label: "Net Wt Kg", numeric: true },
			{ key: "rate", label: "Rate" },
			{ key: "status", label: "Status" },
			{ key: "holding_status", label: "Holding Status" },
			{ key: "warehouse", label: "Warehouse" },
		];

		// Read current filter values
		var filters = {};
		columns.forEach(function (col) {
			var val = $("#flt_" + col.key).val();
			filters[col.key] = (val || "").toLowerCase();
		});

		// Filter rows - preserve original index for S.No
		var filtered = data.filter(function (row, rowIndex) {
			return columns.every(function (col) {
				var fv = filters[col.key];
				if (!fv) return true;
				if (col.key === "sno") {
					var sno = rowIndex + 1;
					return String(sno).toLowerCase().indexOf(fv) !== -1;
				}
				var rv = (row[col.key] == null ? "" : String(row[col.key])).toLowerCase();
				return rv.indexOf(fv) !== -1;
			});
		});

		// Add original index to filtered results for correct S.No display
		var filtered_with_index = filtered.map(function (row, idx) {
			return { row: row, original_index: data.indexOf(row) };
		});

		// Reset to first page when filters change
		current_page = 0;

		// Pagination
		var total_pages = Math.ceil(filtered.length / page_size);
		if (current_page >= total_pages) current_page = Math.max(0, total_pages - 1);
		var start_idx = current_page * page_size;
		var page_data = filtered_with_index.slice(start_idx, start_idx + page_size);

		// Update heading counts
		$("#total_lot_count").text(lotwise_format(data.length) + " Total");
		if (filtered.length !== data.length) {
			$("#filtered_lot_count")
				.text(lotwise_format(filtered.length) + " Filtered")
				.show();
		} else {
			$("#filtered_lot_count").hide();
		}

		var html = `
			<div class="section-body" style="padding:0;">
				<div class="all-lots-wrap">
					<table class="table table-bordered" id="all_lots_table">
						<thead>
							<tr>
		`;

		columns.forEach(function (col) {
			var cur_val = filters[col.key] || "";
			html += `
				<th>
					<span class="col-head">${esc(col.label)}</span>
					<input class="col-filter" id="flt_${col.key}" type="text" value="${esc(
				cur_val
			)}" placeholder="filter" data-col="${col.key}" autocomplete="off" />
				</th>
			`;
		});

		html += `
								</tr>
							</thead>
							<tbody>
		`;

		if (!page_data.length) {
			html += `
				<tr>
					<td colspan="${columns.length}" class="text-center text-muted" style="padding:20px;">
						No matching tea lots found.
					</td>
				</tr>
			`;
		} else {
			page_data.forEach(function (item, idx) {
				var lot = item.row;
				var original_idx = item.original_index;
				html += "<tr>";
				columns.forEach(function (col) {
					var val = lot[col.key];
					if (col.key === "sno") {
						html += "<td>" + (original_idx + 1) + "</td>";
					} else if (col.clickable) {
						// Clickable Tea Lot ID - opens modal
						html +=
							'<td><a href="#" class="lot-detail-link" data-lot="' +
							esc(val) +
							'" style="color:#1f5eff;font-weight:600;text-decoration:none;">' +
							esc(val) +
							"</a></td>";
					} else if (col.numeric) {
						html += "<td>" + (val == null ? "-" : lotwise_format(val)) + "</td>";
					} else if (col.key === "rate") {
						html += "<td>" + money(val) + "</td>";
					} else {
						html += "<td>" + value_or_dash(val) + "</td>";
					}
				});
				html += "</tr>";
			});
		}

		// Pagination controls
		var show_start = filtered.length ? start_idx + 1 : 0;
		var show_end = Math.min(start_idx + page_size, filtered.length);
		var pagination_html = `
			<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-top:1px solid #edf0f4;background:#fbfcfe;">
				<span style="font-size:12px;color:#6b7280;">Showing ${show_start}-${show_end} of ${
			filtered.length
		}</span>
				<div style="display:flex;gap:6px;">
					<button class="btn btn-default btn-sm" id="prev_page_btn" ${
						current_page === 0 ? "disabled" : ""
					}>Previous</button>
					<button class="btn btn-default btn-sm" id="next_page_btn" ${
						current_page >= total_pages - 1 ? "disabled" : ""
					}>Next</button>
				</div>
			</div>
		`;

		html += `
							</tbody>
						</table>
					</div>
				</div>
				${pagination_html}
		`;

		$("#tea_lot_all_container").html(html);

		// Restore focus to the filter input the user was typing in
		if (focused_filter_id) {
			var $input = $("#" + focused_filter_id);
			if ($input.length) {
				$input.focus();
				var inputEl = $input[0];
				if (inputEl.setSelectionRange) {
					inputEl.setSelectionRange(cursor_start, cursor_end);
				}
			}
		}

		// Bind filter input events with debounce
		$("#tea_lot_all_container")
			.off("input", ".col-filter")
			.on("input", ".col-filter", function () {
				if (filter_timeout) clearTimeout(filter_timeout);
				filter_timeout = setTimeout(function () {
					render_all_lots_table();
				}, 200);
			});

		// Bind pagination buttons
		$("#tea_lot_all_container")
			.off("click", "#prev_page_btn")
			.on("click", "#prev_page_btn", function () {
				if (current_page > 0) {
					current_page--;
					render_all_lots_table();
				}
			});
		$("#tea_lot_all_container")
			.off("click", "#next_page_btn")
			.on("click", "#next_page_btn", function () {
				var total_pages = Math.ceil(filtered.length / page_size);
				if (current_page < total_pages - 1) {
					current_page++;
					render_all_lots_table();
				}
			});

		// Bind click on lot detail links
		$("#tea_lot_all_container")
			.off("click", ".lot-detail-link")
			.on("click", ".lot-detail-link", function (e) {
				e.preventDefault();
				var lot_name = $(this).attr("data-lot");
				show_lot_detail_modal(lot_name);
			});
	}

	// ============================================================
	// MODAL: Tea Lot Detail + Evaluation
	// ============================================================

	function show_lot_detail_modal(lot_name) {
		// Create modal if not exists
		var $modal = $("#lot-detail-modal");
		if (!$modal.length) {
			$("body").append(`
				<div class="modal fade" id="lot-detail-modal" tabindex="-1" role="dialog">
					<div class="modal-dialog modal-lg" style="width:90%;max-width:1100px;">
						<div class="modal-content">
							<div class="modal-header">
								<button type="button" class="close" data-dismiss="modal" aria-label="Close">
									<span aria-hidden="true">&times;</span>
								</button>
								<h4 class="modal-title">Tea Lot Details</h4>
							</div>
							<div class="modal-body" style="overflow-x:auto;">
								<div id="lot-detail-modal-body">
									<div class="text-center text-muted" style="padding:30px;">
										<i class="fa fa-spinner fa-spin"></i>
										Loading...
									</div>
								</div>
							</div>
							<div class="modal-footer">
								<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
							</div>
						</div>
					</div>
				</div>
			`);
			$modal = $("#lot-detail-modal");
		}

		$modal.modal("show");

		$("#lot-detail-modal-body").html(`
			<div class="text-center text-muted" style="padding:30px;">
				<i class="fa fa-spinner fa-spin"></i>
				Loading tea lot details...
			</div>
		`);

		// Use the existing get_lot_details API from the main page
		api("tea_lot_dashboard.get_lot_details", { lot_no: lot_name }, function (data) {
			if (!data || !data.lot_details) {
				$("#lot-detail-modal-body").html(`
						<div class="alert alert-info">No Tea Lot details found.</div>
					`);
				return;
			}

			var l = data.lot_details;
			var evaluations = data.evaluations || [];

			var html = build_lot_detail_html(l, evaluations);
			$("#lot-detail-modal-body").html(html);
		});
	}

	// ============================================================
	// BUILD DETAIL HTML (same style as the existing details page)
	// ============================================================

	function build_lot_detail_html(l, evaluations) {
		var html = `
<div style="margin-bottom:20px;">
	<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:0;padding:12px 16px;background:#fbfcfe;border:1px solid #e7eaf0;border-radius:8px 8px 0 0;border-bottom:0;">
		<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
			<h4 style="margin:0;font-size:16px;font-weight:700;color:#1f2937;">Tea Lot Details</h4>
			<span class="lot-badge">${value_or_dash(l.lot_no || l.lot_id)}</span>
			<span class="lot-badge">${value_or_dash(l.invoice_number)}</span>
			<span class="lot-badge">${value_or_dash(l.mark)}</span>
		</div>
	</div>
	<div style="overflow-x:auto;border:1px solid #e7eaf0;border-radius:0 0 8px 8px;">
		<table class="table table-bordered" style="margin-bottom:0;">
			<tr>
				<th style="width:15%;">Lot ID</th>
				<td style="width:35%;">${value_or_dash(l.lot_id)}</td>
				<th style="width:15%;">Lot No</th>
				<td style="width:35%;">${value_or_dash(l.lot_no)}</td>
			</tr>
			<tr>
				<th>Mark</th>
				<td>${value_or_dash(l.mark)}</td>
				<th>Grade</th>
				<td>${value_or_dash(l.grade)}</td>
			</tr>
			<tr>
				<th>Seller</th>
				<td>${value_or_dash(l.seller)}</td>
				<th>Invoice Number</th>
				<td>${value_or_dash(l.invoice_number)}</td>
			</tr>
			<tr>
				<th>Channel</th>
				<td>${value_or_dash(l.acquisition_channel)}</td>
				<th>Status</th>
				<td>${value_or_dash(l.status)}</td>
			</tr>
			<tr>
				<th>Holding Status</th>
				<td>${value_or_dash(l.holding_status)}</td>
				<th>Intended Segment</th>
				<td>${value_or_dash(l.intended_segment)}</td>
			</tr>
			<tr>
				<th>Packages</th>
				<td>${lotwise_format(l.packages)}</td>
				<th>Net Weight</th>
				<td>${lotwise_format(l.net_weight_total)} Kg</td>
			</tr>
			<tr>
				<th>Gross Wt/Pkg</th>
				<td>${lotwise_format(l.gross_wtpkg)} Kg</td>
				<th>Net Wt/Pkg</th>
				<td>${lotwise_format(l.net_wtpkg)} Kg</td>
			</tr>
			<tr>
				<th>Rate</th>
				<td>${money(l.rate)}</td>
				<th>Density</th>
				<td>${lotwise_format(l.density)}</td>
			</tr>
			<tr>
				<th>Packing</th>
				<td>${value_or_dash(l.packing)}</td>
				<th>Liquor Mark</th>
				<td>${value_or_dash(l.liquor_mark)}</td>
			</tr>
			<tr>
				<th>Blend</th>
				<td>${value_or_dash(l.blend)}</td>
				<th>Warehouse</th>
				<td>${value_or_dash(l.warehouse)}</td>
			</tr>
			<tr>
				<th>Purchase Date</th>
				<td>${value_or_dash(l.purchase_date)}</td>
				<th>GP No</th>
				<td>${value_or_dash(l.gp_no)}</td>
			</tr>
			<tr>
				<th>GP Date</th>
				<td>${value_or_dash(l.gp_date)}</td>
				<th>AWR Date</th>
				<td>${value_or_dash(l.awr_date)}</td>
			</tr>
			<tr>
				<th>Broker</th>
				<td>${value_or_dash(l.broker)}</td>
				<th>Sale No</th>
				<td>${value_or_dash(l.sale_no)}</td>
			</tr>
			<tr>
				<th>Centre</th>
				<td>${value_or_dash(l.centre)}</td>
				<th>Division</th>
				<td>${value_or_dash(l.division)}</td>
			</tr>
			<tr>
				<th>Manufacturer Ref</th>
				<td>${value_or_dash(l.manufacturer_ref)}</td>
				<th>Chest Serial Range</th>
				<td>${value_or_dash(l.chest_serial_range)}</td>
			</tr>
			<tr>
				<th>Certification</th>
				<td>${value_or_dash(l.certification)}</td>
				<th>Mfg Month/Year</th>
				<td>${value_or_dash(l.mfg_monthyear)}</td>
			</tr>
			<tr>
				<th>DO Reference</th>
				<td>${value_or_dash(l.do_reference)}</td>
				<th>DO Date</th>
				<td>${value_or_dash(l.do_date)}</td>
			</tr>
			<tr>
				<th>Source Doctype</th>
				<td>${value_or_dash(l.source_doctype)}</td>
				<th>Source ID</th>
				<td>${value_or_dash(l.source_doctype_id)}</td>
			</tr>
		</table>
	</div>
</div>

<div style="border:1px solid #e7eaf0;border-radius:8px;overflow:hidden;">
	<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;background:#fbfcfe;border-bottom:1px solid #edf0f4;">
		<div style="display:flex;align-items:center;gap:10px;">
			<h4 style="margin:0;font-size:16px;font-weight:700;color:#1f2937;">Tea Evaluation</h4>
			<span class="lot-badge">${lotwise_format(evaluations.length)}</span>
		</div>
	</div>
	<div style="overflow-x:auto;">
		${build_evaluation_table(evaluations)}
	</div>
</div>
		`;

		return html;
	}

	function build_evaluation_table(data) {
		if (!data || !data.length) {
			return `<div class="alert alert-info" style="margin:0;border-radius:0;">No Evaluation Found</div>`;
		}

		var html = `
			<table class="table table-bordered" style="margin-bottom:0;">
				<tr>
					<th>Taster</th>
					<th>Stage</th>
					<th>Date</th>
					<th>Colour</th>
					<th>Strength</th>
					<th>Taste</th>
					<th>Briskness</th>
					<th>Quality</th>
					<th>Suggested Value</th>
					<th>Notes</th>
				</tr>
		`;

		data.forEach(function (e) {
			html += `
				<tr>
					<td>${value_or_dash(e.taster)}</td>
					<td>${value_or_dash(e.stage)}</td>
					<td>${value_or_dash(e.evaluation_date)}</td>
					<td>${lotwise_format(e.colour)}</td>
					<td>${lotwise_format(e.strength)}</td>
					<td>${lotwise_format(e.taste)}</td>
					<td>${lotwise_format(e.briskness)}</td>
					<td>${value_or_dash(e.quality_grade)}</td>
					<td>${money(e.suggested_valuation)}</td>
					<td>${value_or_dash(e.notes)}</td>
				</tr>
			`;
		});

		html += "</table>";
		return html;
	}

	// ============================================================
	// PUBLIC API
	// ============================================================

	lotwise.tea_lot_dashboard.load_all_lots = load_all_lots;
})();
