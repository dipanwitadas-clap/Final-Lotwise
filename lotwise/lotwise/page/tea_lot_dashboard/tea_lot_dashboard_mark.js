// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

/* global lotwise */

// ============================================================
// Mark Tab - Search by Mark & Show Tea Lots
// ============================================================

frappe.provide("lotwise.tea_lot_dashboard");

(function () {
	"use strict";

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
		return "₹ " + fmt(value);
	}

	function value_or_dash(value) {
		return value == null || value === "" ? "-" : esc(value);
	}

	function fmt(value) {
		return Number(value || 0).toLocaleString("en-IN", {
			maximumFractionDigits: 2,
		});
	}

	// ============================================================
	// CREATE MARK SEARCH FIELD
	// ============================================================

	function create_mark_search() {
		function run_mark_search() {
			let value = field.get_value() || field.$input.val();
			value = (value || "").trim();
			if (value) {
				load_mark_lots(value);
			} else {
				$("#mark_results").empty();
			}
		}

		let field = frappe.ui.form.make_control({
			parent: $("#mark_search"),
			df: {
				fieldname: "mark",
				label: "Mark",
				fieldtype: "Link",
				options: "Mark",
				placeholder: "Select mark",
				onchange: function () {
					run_mark_search();
				},
			},
			render_input: true,
		});

		field.refresh();
		field.$input.on("keydown", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				run_mark_search();
			}
		});
		field.$input.on("change blur awesomplete-selectcomplete", function () {
			run_mark_search();
		});
	}

	// ============================================================
	// LOAD MARK LOTS
	// ============================================================

	function load_mark_lots(mark) {
		$("#mark_results").html(`
			<div class="detail-box text-center text-muted">
				<i class="fa fa-spinner fa-spin"></i>
				Loading tea lots for this mark...
			</div>
		`);

		api("tea_lot_dashboard_mark.get_lots_by_mark", { mark: mark }, function (data) {
			let lots = (data && data.lots) || [];
			$("#mark_results").html(mark_lot_table(mark, lots));
		});
	}

	// ============================================================
	// RENDER MARK LOT TABLE
	// ============================================================

	function mark_lot_table(mark, lots) {
		if (!lots.length) {
			return `
				<div class="detail-box text-center text-muted">
					No Tea Lots found for mark ${value_or_dash(mark)}.
				</div>
			`;
		}

		let html = `
			<div class="detail-box">
				<div class="section-heading">
					<div class="section-title-wrap">
						<h4>Tea Lots By Mark</h4>
						<span class="lot-badge">${value_or_dash(mark)}</span>
						<span class="lot-badge">${fmt(lots.length)} Lots</span>
					</div>
				</div>
				<div class="section-body">
					<table class="table table-bordered">
						<tr>
							<th>Lot No</th>
							<th>Tea Lot ID</th>
							<th>Grade</th>
							<th>Invoice Number</th>
							<th>Liquor Mark</th>
							<th>Acquisition Channel</th>
							<th>Purchase Date</th>
							<th>Packages</th>
							<th>Net Weight Kg</th>
							<th>Rate</th>
							<th>Status</th>
							<th>Holding Status</th>
						</tr>
		`;

		lots.forEach(function (lot) {
			html += `
				<tr>
					<td>${value_or_dash(lot.lot_no || lot.name)}</td>
					<td>${value_or_dash(lot.name)}</td>
					<td>${value_or_dash(lot.grade)}</td>
					<td>${value_or_dash(lot.invoice_number)}</td>
					<td>${value_or_dash(lot.liquor_mark)}</td>
					<td>${value_or_dash(lot.acquisition_channel)}</td>
					<td>${value_or_dash(lot.purchase_date)}</td>
					<td>${fmt(lot.packages)}</td>
					<td>${fmt(lot.net_weight_total)}</td>
					<td>${money(lot.rate)}</td>
					<td>${value_or_dash(lot.status)}</td>
					<td>${value_or_dash(lot.holding_status)}</td>
				</tr>
			`;
		});

		html += `
					</table>
				</div>
			</div>
		`;
		return html;
	}

	// ============================================================
	// PUBLIC API
	// ============================================================

	lotwise.tea_lot_dashboard.create_mark_search = create_mark_search;
})();
