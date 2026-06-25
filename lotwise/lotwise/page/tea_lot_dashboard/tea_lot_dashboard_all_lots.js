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

	function load_all_lots() {
		$("#tea_lot_all").html(`
			<div class="detail-box text-center text-muted">
				<i class="fa fa-spinner fa-spin"></i>
				Loading all tea lots...
			</div>
		`);

		api("tea_lot_dashboard_all_lots.get_all_lots", {}, function (data) {
			all_lots_data = (data && data.lots) || [];
			render_all_lots_table();
		});
	}

	// ============================================================
	// RENDER FILTERABLE TABLE
	// ============================================================

	function render_all_lots_table() {
		var data = all_lots_data;

		if (!data.length) {
			$("#tea_lot_all").html(`
				<div class="detail-box text-center text-muted">
					No Tea Lots found.
				</div>
			`);
			return;
		}

		var columns = [
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

		// Filter rows
		var filtered = data.filter(function (row) {
			return columns.every(function (col) {
				var fv = filters[col.key];
				if (!fv) return true;
				var rv = (row[col.key] == null ? "" : String(row[col.key])).toLowerCase();
				return rv.indexOf(fv) !== -1;
			});
		});

		var html = `
			<div class="detail-box">
				<div class="section-heading">
					<div class="section-title-wrap">
						<h4>All Tea Lots</h4>
						<span class="lot-count-badge">${lotwise_format(data.length)} Total</span>
						${
							filtered.length !== data.length
								? `<span class="lot-badge" style="background:#fef3c7;color:#92400e;">${lotwise_format(
										filtered.length
								  )} Filtered</span>`
								: ""
						}
					</div>
				</div>
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
			)}" placeholder="filter" data-col="${col.key}" />
				</th>
			`;
		});

		html += `
								</tr>
							</thead>
							<tbody>
		`;

		if (!filtered.length) {
			html += `
				<tr>
					<td colspan="${columns.length}" class="text-center text-muted" style="padding:20px;">
						No matching tea lots found.
					</td>
				</tr>
			`;
		} else {
			filtered.forEach(function (lot) {
				html += "<tr>";
				columns.forEach(function (col) {
					var val = lot[col.key];
					if (col.clickable) {
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

		html += `
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`;

		$("#tea_lot_all").html(html);

		// Bind filter input events with debounce
		$("#tea_lot_all .col-filter").on("input", function () {
			if (filter_timeout) clearTimeout(filter_timeout);
			filter_timeout = setTimeout(function () {
				render_all_lots_table();
			}, 200);
		});

		// Bind click on lot detail links
		$("#tea_lot_all").on("click", ".lot-detail-link", function (e) {
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
