// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

/* global lotwise */

// ============================================================
// Evaluation Tab - Search & Filter Tea Evaluations
// ============================================================

frappe.provide("lotwise.tea_lot_dashboard");

(function () {
	"use strict";

	var taster_field = null;

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
	// CREATE EVALUATION SEARCH FIELD
	// ============================================================

	function create_evaluation_search() {
		function run_evaluation_search() {
			load_evaluations();
		}

		$("#eval_search_btn").on("click", function () {
			run_evaluation_search();
		});

		$("#eval_clear_btn").on("click", function () {
			$("#eval_colour").val("");
			$("#eval_strength").val("");
			$("#eval_taste").val("");
			$("#eval_briskness").val("");
			$("#eval_quality_grade").val("");
			if (taster_field) {
				taster_field.set_value("");
			}
			$("#eval_stage").val("");
			$("#evaluation_results").empty();
		});

		taster_field = frappe.ui.form.make_control({
			parent: $("#eval_taster_field"),
			df: {
				fieldname: "taster",
				label: "Taster",
				fieldtype: "Link",
				options: "Taster",
				placeholder: "Select taster",
				onchange: function () {
					run_evaluation_search();
				},
			},
			render_input: true,
		});

		taster_field.refresh();
	}

	// ============================================================
	// LOAD EVALUATIONS
	// ============================================================

	function load_evaluations() {
		let args = {};

		let colour = $("#eval_colour").val().trim();
		let strength = $("#eval_strength").val().trim();
		let taste = $("#eval_taste").val().trim();
		let briskness = $("#eval_briskness").val().trim();
		let quality_grade = $("#eval_quality_grade").val();
		let stage = $("#eval_stage").val();

		let taster_val = "";
		if (taster_field) {
			taster_val = (taster_field.get_value() || "").trim();
		}

		if (colour) args.colour = colour;
		if (strength) args.strength = strength;
		if (taste) args.taste = taste;
		if (briskness) args.briskness = briskness;
		if (quality_grade) args.quality_grade = quality_grade;
		if (taster_val) args.taster = taster_val;
		if (stage) args.stage = stage;

		$("#evaluation_results").html(`
			<div class="detail-box text-center text-muted">
				<i class="fa fa-spinner fa-spin"></i>
				Loading evaluations...
			</div>
		`);

		api("tea_lot_dashboard_evaluation.get_evaluations", args, function (data) {
			let evals = (data && data.evaluations) || [];
			$("#evaluation_results").html(evaluation_results_table(evals));
		});
	}

	// ============================================================
	// RENDER EVALUATION RESULTS TABLE
	// ============================================================

	function evaluation_results_table(evals) {
		if (!evals.length) {
			return `
				<div class="detail-box text-center text-muted">
					No Evaluations found.
				</div>
			`;
		}

		let html = `
			<div class="detail-box">
				<div class="section-heading">
					<div class="section-title-wrap">
						<h4>Tea Evaluation Results</h4>
						<span class="lot-badge">${fmt(evals.length)} Records</span>
					</div>
				</div>
				<div class="section-body" style="overflow-x:auto;">
					<table class="table table-bordered">
						<tr>
							<th>Tea Evaluation ID</th>
							<th>Tea Lot</th>
							<th>Lot No</th>
							<th>Mark</th>
							<th>Colour</th>
							<th>Strength</th>
							<th>Taste</th>
							<th>Briskness</th>
							<th>Quality Grade</th>
							<th>Taster</th>
							<th>Stage</th>
							<th>Eval Date</th>
							<th>Suggested Valuation</th>
							<th>Notes</th>
						</tr>
		`;

		evals.forEach(function (e) {
			html += `
				<tr>
					<td>${value_or_dash(e.name)}</td>
					<td>${value_or_dash(e.tea_lot)}</td>
					<td>${value_or_dash(e.tea_lot_no)}</td>
					<td>${value_or_dash(e.tea_lot_mark)}</td>
					<td>${fmt(e.colour)}</td>
					<td>${fmt(e.strength)}</td>
					<td>${fmt(e.taste)}</td>
					<td>${fmt(e.briskness)}</td>
					<td>${value_or_dash(e.quality_grade)}</td>
					<td>${value_or_dash(e.taster)}</td>
					<td>${value_or_dash(e.stage)}</td>
					<td>${value_or_dash(e.evaluation_date)}</td>
					<td>${money(e.suggested_valuation)}</td>
					<td>${value_or_dash(e.notes)}</td>
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

	lotwise.tea_lot_dashboard.create_evaluation_search = create_evaluation_search;
	lotwise.tea_lot_dashboard.load_evaluations = load_evaluations;
})();
