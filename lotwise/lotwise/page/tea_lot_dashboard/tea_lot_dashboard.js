// // Copyright (c) 2026, BusinessThat.Works and contributors
// // For license information, please see license.txt

// frappe.pages["tea-lot-dashboard"].on_page_load = function (wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: __("Tea Lot Dashboard"),
// 		single_column: true,
// 	});

// 	// Toolbar
// 	page.add_inner_button(__("+ Tea Lot"), () => frappe.new_doc("Tea Lot"));
// 	page.add_inner_button(__("+ Evaluation"), () => frappe.new_doc("Tea Evaluation"));
// 	page.add_inner_button(__("Import"), () => frappe.new_doc("Tea Lot Import"));
// 	page.add_inner_button(__("Holding Report"), () => frappe.set_route("query-report", "Holding Warhouse"));
// 	page.add_inner_button(__("Refresh"), () => frappe.set_route("page", "tea-lot-dashboard"));

// 	// Styles
// 	$("<style>").prop("type", "text/css").html(`
// 		.search-card {
// 			background: linear-gradient(135deg, #1e1b4b, #1a1a2e) !important;
// 			border: 1px solid rgba(168,85,247,0.3) !important;
// 			border-radius: 12px !important;
// 			box-shadow: 0 4px 16px rgba(168,85,247,0.12) !important;
// 		}
// 		.search-card .card-body { color: #e2e8f0 !important; }
// 		.search-card h6 { color: #e2e8f0 !important; font-weight: 700 !important; }
// 		.search-card .form-control, .search-card input {
// 			background: rgba(255,255,255,0.08) !important;
// 			border: 1px solid rgba(168,85,247,0.4) !important;
// 			color: #e2e8f0 !important;
// 			border-radius: 8px !important;
// 		}
// 		.search-card .form-control:focus, .search-card input:focus {
// 			border-color: #a855f7 !important;
// 			box-shadow: 0 0 0 2px rgba(168,85,247,0.25) !important;
// 		}
// 		.search-card .awesomplete input {
// 			background: rgba(255,255,255,0.08) !important;
// 			border: 1px solid rgba(168,85,247,0.4) !important;
// 			color: #e2e8f0 !important;
// 			border-radius: 8px !important;
// 		}
// 		.lot-profile-header {
// 			background: linear-gradient(135deg, #2563eb, #0891b2, #7c3aed) !important;
// 			border-radius: 12px !important;
// 			padding: 20px 24px !important;
// 			box-shadow: 0 4px 16px rgba(37,99,235,0.25) !important;
// 			margin-bottom: 16px !important;
// 			display: flex !important;
// 			align-items: center !important;
// 			gap: 20px !important;
// 			color: #fff !important;
// 		}
// 		.lot-avatar {
// 			width: 60px !important;
// 			height: 60px !important;
// 			border-radius: 50% !important;
// 			background: rgba(255,255,255,0.2) !important;
// 			border: 2px solid rgba(255,255,255,0.4) !important;
// 			display: flex !important;
// 			align-items: center !important;
// 			justify-content: center !important;
// 			font-size: 28px !important;
// 			flex-shrink: 0 !important;
// 		}
// 		.lot-profile-info h3 { margin: 0 0 6px 0 !important; font-size: 20px !important; }
// 		.lot-meta { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
// 		.meta-item {
// 			background: rgba(255,255,255,0.2) !important;
// 			padding: 4px 12px !important;
// 			border-radius: 20px !important;
// 			font-size: 12px !important;
// 			font-weight: 600 !important;
// 		}
// 		.eval-card {
// 			border-left: 4px solid !important;
// 			margin-bottom: 8px !important;
// 			padding: 12px !important;
// 			background: #f8f9fa !important;
// 			border-radius: 4px !important;
// 		}
// 	`).appendTo("head");

// 	// Main content
// 	$(page.body).html(`
// 		<div class="container" style="padding:20px;">
// 			<div class="row" style="margin-bottom:15px;" id="stats-container"></div>

// 			<div class="row" style="margin-bottom:15px;">
// 				<div class="col-sm-4"><div class="frappe-card"><div class="card-body" id="chart-channel"></div></div></div>
// 				<div class="col-sm-4"><div class="frappe-card"><div class="card-body" id="chart-hold"></div></div></div>
// 				<div class="col-sm-4"><div class="frappe-card"><div class="card-body" id="chart-status"></div></div></div>
// 			</div>

// 			<div class="row" style="margin-bottom:15px;" id="eval-row"></div>

// 			<div class="card search-card" style="margin-bottom:15px;">
// 				<div class="card-body">
// 					<h6 style="margin-bottom:8px;"><i class="fa fa-search"></i> Search Tea Lot</h6>
// 					<div id="lot_link_container"></div>
// 					<p style="font-size:12px;color:#94a3b8;margin-top:4px;">
// 						<i class="fa fa-info-circle"></i> Type lot number, mark, grade or invoice number
// 					</p>
// 				</div>
// 			</div>

// 			<div id="lot-details-container"></div>
// 		</div>
// 	`);

// 	// Lot search field
// 	var lot_field = frappe.ui.form.make_control({
// 		parent: $("#lot_link_container"),
// 		df: {
// 			label: "Tea Lot",
// 			fieldname: "lot_no",
// 			fieldtype: "Link",
// 			options: "Tea Lot",
// 			placeholder: "Search by lot number, mark, grade...",
// 			get_query: function() {
// 				return {
// 					query: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.lot_query"
// 				};
// 			},
// 			onchange: function() {
// 				var val = lot_field.get_value();
// 				if (val) {
// 					load_lot(val);
// 				} else {
// 					$("#lot-details-container").empty();
// 				}
// 			}
// 		},
// 		render_input: true
// 	});
// 	lot_field.refresh();

// 	// Helpers
// 	function num(v, d) {
// 		if (v == null) return "0";
// 		return Number(v).toLocaleString("en-IN", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 });
// 	}

// 	function esc(s) {
// 		if (!s) return "";
// 		return String(s).replace(/[&<>"]/g, function(m) {
// 			if (m === "&") return "\x26amp;";
// 			if (m === "<") return "\x3Clt;";
// 			if (m === ">") return "\x3Egt;";
// 			return "\x22quot;";
// 		});
// 	}

// 	// Stats
// 	function load_stats() {
// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_summary_stats",
// 			callback: function(r) {
// 				if (!r.message) return;
// 				var d = r.message;
// 				var h = "";
// 				var cards = [
// 					{ l: "Total Lots", v: d.total_lots, i: "fa-cubes", c: "#2490ef" },
// 					{ l: "Packages", v: num(d.total_packages, 0), i: "fa-cube", c: "#5cb85c" },
// 					{ l: "Net Wt (kg)", v: num(d.total_net_weight, 1), i: "fa-balance-scale", c: "#f0ad4e" },
// 					{ l: "Avg Rate/kg", v: "\u20B9 " + num(d.avg_rate, 2), i: "fa-money", c: "#d9534f" },
// 					{ l: "Marks", v: d.unique_marks, i: "fa-tag", c: "#5bc0de" },
// 					{ l: "Grades", v: d.unique_grades, i: "fa-sort-alpha-asc", c: "#9274b3" },
// 					{ l: "Evaluations", v: d.total_evaluations, i: "fa-star", c: "#66bb6a" },
// 				];
// 				// Row 1: first 4
// 				var r1 = cards.slice(0,4).map(function(c) {
// 					return '<div class="col-sm-3"><div class="frappe-card text-center" style="padding:15px 8px;"><div style="font-size:24px;color:' + c.c + ';margin-bottom:2px;"><i class="fa ' + c.i + '"></i></div><div style="font-size:22px;font-weight:700;">' + c.v + '</div><div class="text-muted" style="font-size:10px;text-transform:uppercase;">' + c.l + '</div></div></div>';
// 				}).join("");
// 				// Row 2: last 3
// 				var r2 = cards.slice(4).map(function(c) {
// 					return '<div class="col-sm-4"><div class="frappe-card text-center" style="padding:15px 8px;"><div style="font-size:24px;color:' + c.c + ';margin-bottom:2px;"><i class="fa ' + c.i + '"></i></div><div style="font-size:22px;font-weight:700;">' + c.v + '</div><div class="text-muted" style="font-size:10px;text-transform:uppercase;">' + c.l + '</div></div></div>';
// 				}).join("");
// 				$("#stats-container").html('<div class="col-sm-12"><div class="row" style="margin-bottom:8px;">' + r1 + '</div><div class="row">' + r2 + '</div></div>');
// 			}
// 		});
// 	}

// 	// Charts
// 	function load_charts() {
// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_channel_distribution",
// 			callback: function(r) { make_chart("chart-channel", "Channel", r.message); }
// 		});
// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_holding_status_distribution",
// 			callback: function(r) { make_chart("chart-hold", "Holding", r.message); }
// 		});
// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_status_distribution",
// 			callback: function(r) { make_chart("chart-status", "Status", r.message); }
// 		});
// 	}

// 	function make_chart(id, title, data) {
// 		if (!data || !data.length) return;
// 		new frappe.Chart("#" + id, {
// 			title: title,
// 			data: { labels: data.map(function(d){return d.name;}), datasets: [{values: data.map(function(d){return d.value;})}] },
// 			type: "pie",
// 			height: 180,
// 			colors: ["#2490ef","#5b8def","#8bafe8","#f0ad4e","#5cb85c","#d9534f","#9274b3","#66bb6a"],
// 		});
// 	}

// 	// Overall eval scores
// 	function load_eval_overall() {
// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_evaluation_summary",
// 			callback: function(r) {
// 				if (!r.message) return;
// 				var d = r.message;
// 				var scores = [
// 					{ label: "Colour", val: Math.round((d.avg_colour||0)*10)/10, clr: "#d9534f" },
// 					{ label: "Strength", val: Math.round((d.avg_strength||0)*10)/10, clr: "#f0ad4e" },
// 					{ label: "Taste", val: Math.round((d.avg_taste||0)*10)/10, clr: "#5cb85c" },
// 					{ label: "Briskness", val: Math.round((d.avg_briskness||0)*10)/10, clr: "#2490ef" }
// 				];
// 				var h = '<div class="col-sm-12"><div class="frappe-card"><div class="card-body">';
// 				h += '<h6 style="margin:0 0 10px 0;font-weight:700;"><i class="fa fa-star text-warning"></i> Overall Avg Evaluation Scores (' + (d.total_evaluations||0) + ' total)</h6><div class="row">';
// 				scores.forEach(function(s) {
// 					var pct = Math.round((s.val / 10) * 100);
// 					h += '<div class="col-sm-3 text-center"><div style="font-size:26px;font-weight:700;color:' + s.clr + ';">' + s.val + '</div><div class="progress" style="height:6px;margin:4px 0;background:#eee;border-radius:3px;"><div class="progress-bar" style="width:' + pct + '%;background:' + s.clr + ';border-radius:3px;"></div></div><div style="font-size:11px;color:#6c757d;font-weight:600;">' + s.label + '</div></div>';
// 				});
// 				h += '</div></div></div></div>';
// 				$("#eval-row").html(h);
// 			}
// 		});
// 	}

// 	// Load lot details
// 	function load_lot(lot_no) {
// 		$("#lot-details-container").html('<div class="text-center py-5"><i class="fa fa-spinner fa-spin fa-2x text-muted"></i><p class="mt-2 text-muted">Loading lot details...</p></div>');

// 		frappe.call({
// 			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.get_lot_details",
// 			args: { lot_no: lot_no },
// 			callback: function(r) {
// 				if (r && r.message) {
// 					render_lot(r.message);
// 				} else {
// 					$("#lot-details-container").html('<div class="text-center py-5 text-muted"><i class="fa fa-exclamation-triangle fa-2x"></i><h5>No Data Found</h5></div>');
// 				}
// 			},
// 			error: function() {
// 				$("#lot-details-container").html('<div class="text-center py-5 text-danger"><i class="fa fa-exclamation-circle fa-2x"></i><h5>Error Loading Data</h5></div>');
// 			}
// 		});
// 	}

// 	function render_lot(data) {
// 		var lot = data.lot || {};
// 		var evals = data.evaluations || [];
// 		var esum = data.eval_summary || {};

// 		var st_badge = lot.status === "Evaluated"
// 			? '<span class="badge badge-success" style="font-size:11px;">Evaluated</span>'
// 			: '<span class="badge badge-secondary" style="font-size:11px;">Offered</span>';

// 		var h = '';

// 		// Profile Header
// 		h += '<div class="lot-profile-header"><div class="lot-avatar"><i class="fa fa-cubes"></i></div><div class="lot-profile-info">';
// 		h += '<h3>' + esc(lot.name) + '</h3>';
// 		h += '<div class="lot-meta">';
// 		h += '<span class="meta-item"><i class="fa fa-tag"></i> ' + esc(lot.mark || "-") + '</span>';
// 		h += '<span class="meta-item"><i class="fa fa-sort-alpha-asc"></i> ' + esc(lot.grade || "-") + '</span>';
// 		h += '<span class="meta-item"><i class="fa fa-shopping-cart"></i> ' + esc(lot.acquisition_channel || "-") + '</span>';
// 		h += '<span class="meta-item"><i class="fa fa-archive"></i> ' + esc(lot.holding_status || "-") + '</span>';
// 		h += st_badge;
// 		h += '</div></div></div>';

// 		// Lot Info Table
// 		h += '<div class="card" style="margin-bottom:15px;"><div class="card-body">';
// 		h += '<h6 style="font-weight:700;margin:0 0 10px 0;color:#2563eb;"><i class="fa fa-info-circle"></i> Lot Information</h6>';
// 		h += '<table class="table table-bordered table-sm" style="margin:0;font-size:12px;">';
// 		h += '<tr><th class="bg-light" width="15%">Lot ID</th><td width="35%"><b>' + esc(lot.name) + '</b></td><th class="bg-light" width="15%">Lot No</th><td width="35%">' + esc(lot.lot_no) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Mark</th><td><b>' + esc(lot.mark) + '</b></td><th class="bg-light">Grade</th><td>' + esc(lot.grade) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Channel</th><td><span class="label label-primary">' + esc(lot.acquisition_channel) + '</span></td><th class="bg-light">Status</th><td>' + esc(lot.status) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Holding</th><td>' + esc(lot.holding_status) + '</td><th class="bg-light">Segment</th><td>' + esc(lot.intended_segment) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Seller</th><td>' + esc(lot.seller) + '</td><th class="bg-light">Invoice</th><td>' + esc(lot.invoice_number) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Packages</th><td><b>' + num(lot.packages, 0) + '</b></td><th class="bg-light">Net Wt (kg)</th><td><b>' + num(lot.net_weight_total, 2) + '</b></td></tr>';
// 		h += '<tr><th class="bg-light">Rate/kg</th><td><b>\u20B9 ' + num(lot.rate, 2) + '</b></td><th class="bg-light">Density</th><td>' + num(lot.density, 2) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Liquor Mark</th><td>' + esc(lot.liquor_mark) + '</td><th class="bg-light">Blend</th><td>' + esc(lot.blend) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Warehouse</th><td>' + esc(lot.warehouselocation) + '</td><th class="bg-light">Purchase Date</th><td>' + esc(lot.purchase_date) + '</td></tr>';
// 		h += '<tr><th class="bg-light">GP No</th><td>' + esc(lot.gp_no) + '</td><th class="bg-light">GP Date</th><td>' + esc(lot.gp_date) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Broker</th><td>' + esc(lot.broker) + '</td><th class="bg-light">Sale No</th><td>' + esc(lot.sale_no) + '</td></tr>';
// 		h += '<tr><th class="bg-light">Centre</th><td>' + esc(lot.centre) + '</td><th class="bg-light">Certification</th><td>' + esc(lot.certification) + '</td></tr>';
// 		h += '<tr><th class="bg-light">DO Ref</th><td>' + esc(lot.do_reference) + '</td><th class="bg-light">DO Date</th><td>' + esc(lot.do_date) + '</td></tr>';
// 		h += '<tr><th class="bg-light">AWR Date</th><td>' + esc(lot.awr_date) + '</td><th class="bg-light">MFG</th><td>' + esc(lot.mfg_monthyear) + '</td></tr>';
// 		h += '</table></div></div>';

// 		// Evaluations Section
// 		if (!evals || evals.length === 0) {
// 			h += '<div class="card"><div class="card-body text-center py-4 text-muted"><i class="fa fa-star-o fa-3x mb-2"></i><h5>No Evaluations Yet</h5><p>This lot has not been evaluated.</p></div></div>';
// 		} else {
// 			h += '<div class="card" style="margin-bottom:15px;"><div class="card-body">';
// 			h += '<h5 style="font-weight:700;margin:0 0 12px 0;color:#2563eb;"><i class="fa fa-star text-warning"></i> Tea Evaluations (' + evals.length + ')</h5>';

// 			// Average scores
// 			h += '<h6 style="font-weight:600;margin:0 0 10px 0;">Average Scores</h6><div class="row" style="margin-bottom:15px;">';
// 			var avg_scores = [
// 				{ label: "Colour", val: Math.round((esum.avg_colour||0)*10)/10, clr: "#d9534f" },
// 				{ label: "Strength", val: Math.round((esum.avg_strength||0)*10)/10, clr: "#f0ad4e" },
// 				{ label: "Taste", val: Math.round((esum.avg_taste||0)*10)/10, clr: "#5cb85c" },
// 				{ label: "Briskness", val: Math.round((esum.avg_briskness||0)*10)/10, clr: "#2490ef" },
// 			];
// 			avg_scores.forEach(function(s) {
// 				var pct = Math.round((s.val / 10) * 100);
// 				h += '<div class="col-sm-3 text-center"><div style="font-size:22px;font-weight:700;color:' + s.clr + ';">' + s.val + '</div><div class="progress" style="height:6px;margin:4px 0;background:#eee;border-radius:3px;"><div class="progress-bar" style="width:' + pct + '%;background:' + s.clr + ';border-radius:3px;"></div></div><div style="font-size:11px;color:#6c757d;font-weight:600;">' + s.label + '</div></div>';
// 			});
// 			h += '</div>';

// 			// Each evaluation card
// 			h += '<h6 style="font-weight:600;margin:0 0 10px 0;">Evaluation Details</h6>';
// 			evals.forEach(function(e) {
// 				var bc = e.quality_grade ? "#f0ad4e" : "#6c757d";
// 				h += '<div class="eval-card" style="border-left-color:' + bc + ';">';
// 				h += '<div class="row"><div class="col-sm-2 text-center"><div style="font-size:11px;color:#6c757d;font-weight:600;">Taster</div><div style="font-weight:700;">' + esc(e.taster) + '</div><div><span class="label label-info" style="font-size:10px;">' + esc(e.stage) + '</span></div></div>';
// 				h += '<div class="col-sm-2 text-center"><div style="font-size:11px;color:#6c757d;font-weight:600;">Date</div><div>' + (e.evaluation_date || "-") + '</div><div>' + (e.quality_grade ? '<span class="badge badge-warning" style="font-size:11px;">' + esc(e.quality_grade) + '</span>' : "-") + '</div></div>';
// 				h += '<div class="col-sm-2 text-center"><div style="font-size:11px;color:#d9534f;font-weight:600;">Colour</div><div style="font-size:18px;font-weight:700;color:#d9534f;">' + num(e.colour, 1) + '</div></div>';
// 				h += '<div class="col-sm-2 text-center"><div style="font-size:11px;color:#f0ad4e;font-weight:600;">Strength</div><div style="font-size:18px;font-weight:700;color:#f0ad4e;">' + num(e.strength, 1) + '</div></div>';
// 				h += '<div class="col-sm-2 text-center"><div style="font-size:11px;color:#5cb85c;font-weight:600;">Taste</div><div style="font-size:18px;font-weight:700;color:#5cb85c;">' + num(e.taste, 1) + '</div></div>';
// 				h += '<div class="col-sm-2 text-center"><div style="font-size:11px;color:#2490ef;font-weight:600;">Briskness</div><div style="font-size:18px;font-weight:700;color:#2490ef;">' + num(e.briskness, 1) + '</div></div></div>';
// 				h += '<div class="row" style="margin-top:6px;"><div class="col-sm-2 text-center"><div style="font-size:11px;color:#6c757d;font-weight:600;">Valuation</div><div style="font-weight:700;">\u20B9 ' + num(e.suggested_valuation, 0) + '</div></div>';
// 				h += '<div class="col-sm-10"><div style="font-size:11px;color:#6c757d;font-weight:600;">Notes</div><div style="font-size:12px;">' + esc(e.notes || "-") + '</div></div></div>';
// 				h += '</div>';
// 			});
// 			h += '</div></div>';
// 		}

// 		$("#lot-details-container").html(h);
// 	}

// 	// Init
// 	load_stats();
// 	load_charts();
// 	load_eval_overall();
// };
// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.pages["tea-lot-dashboard"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,

		title: __("Tea Lot Dashboard"),

		single_column: true,
	});

	// --------------------------------------------------
	// BUTTONS
	// --------------------------------------------------

	page.add_inner_button(__("New Tea Lot"), () => frappe.new_doc("Tea Lot"));

	page.add_inner_button(__("New Evaluation"), () => frappe.new_doc("Tea Evaluation"));

	page.add_inner_button(__("Import Data"), () => frappe.new_doc("Tea Lot Import"));

	page.add_inner_button(__("Holding Warehouse"), () => {
		frappe.set_route("query-report", "Holding Warhouse");
	});

	// --------------------------------------------------
	// MAIN HTML
	// --------------------------------------------------

	$(page.main).html(`


<style>

.dashboard-card{

	background:white;

	border-radius:10px;

	padding:12px;

	box-shadow:
	0 1px 5px rgba(0,0,0,.1);

	text-align:center;

	height:100px;

}



.dashboard-card h3{

	margin:5px;

	font-size:22px;

}



.dashboard-card small{

	color:#777;

}



.detail-box{

	background:white;

	border-radius:10px;

	padding:20px;

	margin-top:20px;

	box-shadow:
	0 1px 5px rgba(0,0,0,.1);

}



.lot-search-card{

	background:white;

	border-radius:10px;

	padding:16px;

	box-shadow:
	0 1px 5px rgba(0,0,0,.1);

}



.lot-details-heading{

	display:flex;

	justify-content:space-between;

	align-items:center;

	gap:12px;

	margin-bottom:15px;

}



.lot-details-heading h4{

	margin:0;

}



.lot-badge{

	background:#eef6ff;

	color:#1f5eff;

	border-radius:999px;

	padding:4px 10px;

	font-size:12px;

	font-weight:600;

}



.lot-table-wrap{

	overflow-x:auto;

}



.table th{

	background:#f5f5f5;

}



</style>



<div class="tea-dashboard">


<div class="row"
id="cards">

</div>



<div class="row"
style="margin-top:20px">

<div class="col-md-6">

<div class="lot-search-card">

<div id="lot_search"></div>

<div class="text-muted"
style="font-size:12px;margin-top:6px">
Search by lot no, mark, grade, seller or invoice number.
</div>

</div>


</div>


</div>




<div id="lot_details">


</div>



</div>



`);

	// --------------------------------------------------
	// API CALL
	// --------------------------------------------------

	function api(method, args = {}, callback) {
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard." + method,

			args: args,

			callback: function (r) {
				callback(r.message);
			},

			error: function () {
				callback(null);
			},
		});
	}

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function money(value) {
		return "₹ " + format(value);
	}

	function value_or_dash(value) {
		return value == null || value === "" ? "-" : esc(value);
	}

	// --------------------------------------------------
	// SUMMARY CARDS
	// --------------------------------------------------

	function load_cards() {
		api("get_summary_stats", {}, function (data) {
			let cards = [
				["Total Lots", data.total_lots],

				["Packages", data.total_packages],

				["Net Weight Kg", data.total_net_weight],

				["Avg Rate/kg", "₹ " + format(data.avg_rate)],

				["Marks", data.unique_marks],

				["Grades", data.unique_grades],

				["Evaluations", data.total_evaluations],
			];

			let html = "";

			cards.forEach(function (c) {
				html += `


					<div class="col-md"
					style="
					flex:1;
					padding:5px;
					">


					<div class="dashboard-card">


					<h3>
					${c[1] || 0}
					</h3>


					<small>
					${c[0]}
					</small>



					</div>


					</div>


					`;
			});

			$("#cards").html(html);
		});
	}

	// --------------------------------------------------
	// LOT SEARCH FIELD
	// --------------------------------------------------

	function create_lot_search() {
		function run_lot_search() {
			let value = field.get_value() || field.$input.val();

			value = (value || "").trim();

			if (value) {
				load_lot_details(value);
			} else {
				$("#lot_details").empty();
			}
		}

		let field = frappe.ui.form.make_control({
			parent: $("#lot_search"),

			df: {
				fieldname: "tea_lot",

				label: "Lot No",

				fieldtype: "Link",

				options: "Tea Lot",

				placeholder: "Type lot no, mark, grade, seller or invoice",

				get_query: function () {
					return {
						query: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard.lot_query",
					};
				},

				onchange: function () {
					run_lot_search();
				},
			},

			render_input: true,
		});

		field.refresh();

		field.$input.on("keydown", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();

				run_lot_search();
			}
		});

		field.$input.on("change blur awesomplete-selectcomplete", function () {
			run_lot_search();
		});
	}

	// --------------------------------------------------
	// LOT DETAILS
	// --------------------------------------------------

	function load_lot_details(lot) {
		$("#lot_details").html(`
			<div class="detail-box text-center text-muted">
				<i class="fa fa-spinner fa-spin"></i>
				Loading tea lot details...
			</div>
		`);

		api(
			"get_lot_details",

			{
				lot_no: lot,
			},

			function (data) {
				if (!data) {
					$("#lot_details").html(`
						<div class="detail-box text-center text-muted">
							No Tea Lot found for this ID.
						</div>
					`);

					return;
				}

				let l = data.lot_details;

				if (!l) {
					$("#lot_details").html(`
						<div class="detail-box text-center text-muted">
							No Tea Lot details found.
						</div>
					`);

					return;
				}

				let html = `



<div class="detail-box">


<div class="lot-details-heading">
<h4>Tea Lot Details</h4>
<span class="lot-badge">${value_or_dash(l.lot_no || l.lot_id)}</span>
</div>

<div class="lot-table-wrap">

<table class="table table-bordered">


<tr>

<th>Lot ID</th>
<td>${value_or_dash(l.lot_id)}</td>

<th>Lot No</th>
<td>${value_or_dash(l.lot_no)}</td>

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

<td>${format(l.packages)}</td>


<th>Net Weight</th>

<td>${format(l.net_weight_total)} Kg</td>


</tr>


<tr>

<th>Gross Wt/Pkg</th>
<td>${format(l.gross_wtpkg)} Kg</td>

<th>Net Wt/Pkg</th>
<td>${format(l.net_wtpkg)} Kg</td>

</tr>



<tr>

<th>Rate</th>

<td>${money(l.rate)}</td>


<th>Density</th>

<td>${format(l.density)}</td>


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

<h4 style="margin-top:20px">
Tea Evaluation
</h4>


${evaluation_table(data.evaluations)}



</div>


`;

				$("#lot_details").html(html);
			}
		);
	}

	function evaluation_table(data) {
		if (!data || !data.length) {
			return `

			<div class="alert alert-info">

			No Evaluation Found

			</div>

			`;
		}

		let html = `


<table class="table table-bordered">


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

<td>${format(e.colour)}</td>

<td>${format(e.strength)}</td>

<td>${format(e.taste)}</td>

<td>${format(e.briskness)}</td>

<td>${value_or_dash(e.quality_grade)}</td>

<td>${money(e.suggested_valuation)}</td>

<td>${value_or_dash(e.notes)}</td>


</tr>


`;
		});

		html += "</table>";

		return html;
	}

	function format(value) {
		return Number(value || 0).toLocaleString("en-IN", {
			maximumFractionDigits: 2,
		});
	}

	// INITIAL LOAD

	load_cards();

	create_lot_search();
};
