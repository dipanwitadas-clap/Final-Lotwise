// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

/* global lotwise */

// ============================================================
// Grade Tab - Search by Grade & Show Tea Lots
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
	// CREATE GRADE SEARCH FIELD
	// ============================================================

	function create_grade_search() {
		function run_grade_search() {
			let value = field.get_value() || field.$input.val();
			value = (value || "").trim();
			if (value) {
				load_grade_lots(value);
			} else {
				$("#grade_results").empty();
			}
		}

		let field = frappe.ui.form.make_control({
			parent: $("#grade_search"),
			df: {
				fieldname: "grade",
				label: "Grade",
				fieldtype: "Link",
				options: "Grade",
				placeholder: "Select grade",
				onchange: function () {
					run_grade_search();
				},
			},
			render_input: true,
		});

		field.refresh();
		field.$input.on("keydown", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				run_grade_search();
			}
		});
		field.$input.on("change blur awesomplete-selectcomplete", function () {
			run_grade_search();
		});
	}

	// ============================================================
	// LOAD GRADE LOTS
	// ============================================================

	function load_grade_lots(grade) {
		$("#grade_results").html(`
			<div class="detail-box text-center text-muted">
				<i class="fa fa-spinner fa-spin"></i>
				Loading tea lots for this grade...
			</div>
		`);

		api("tea_lot_dashboard_grade.get_lots_by_grade", { grade: grade }, function (data) {
			let lots = (data && data.lots) || [];
			$("#grade_results").html(grade_lot_table(grade, lots));
		});
	}

	// ============================================================
	// RENDER GRADE LOT TABLE
	// ============================================================

	function grade_lot_table(grade, lots) {
		if (!lots.length) {
			return `
				<div class="detail-box text-center text-muted">
					No Tea Lots found for grade ${value_or_dash(grade)}.
				</div>
			`;
		}

		let html = `
			<div class="detail-box">
				<div class="section-heading">
					<div class="section-title-wrap">
						<h4>Tea Lots By Grade</h4>
						<span class="lot-badge">${value_or_dash(grade)}</span>
						<span class="lot-badge">${fmt(lots.length)} Lots</span>
					</div>
				</div>
				<div class="section-body">
					<table class="table table-bordered">
						<tr>
							<th>Lot No</th>
							<th>Tea Lot ID</th>
							<th>Mark</th>
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
					<td>${value_or_dash(lot.mark)}</td>
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

	lotwise.tea_lot_dashboard.create_grade_search = create_grade_search;
})();
