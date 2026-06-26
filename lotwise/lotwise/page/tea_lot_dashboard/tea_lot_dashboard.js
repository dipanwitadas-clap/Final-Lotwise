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
	page.add_inner_button(__("Tea Lot Data Import"), () => frappe.new_doc("Tea Lot Import"));
	page.add_inner_button(__("Holding Warehouse"), () => {
		frappe.set_route("query-report", "Holding Warhouse");
	});

	// --------------------------------------------------
	// MAIN HTML
	// --------------------------------------------------

	$(page.main).html(`


<style>

.tea-dashboard{
	background:#f6f7fb;
	margin:-20px;
	padding:20px;
	min-height:calc(100vh - 120px);
}
.tea-dashboard .row{
	margin-left:-6px;
	margin-right:-6px;
}
.dashboard-card{
	background:white;
	border:1px solid #e7eaf0;
	border-radius:8px;
	padding:14px 16px;
	box-shadow:0 1px 3px rgba(15,23,42,.08);
	display:flex;
	align-items:center;
	gap:12px;
	min-height:88px;
	height:100%;
	border-left:4px solid var(--card-accent,#4f8df7);
}
.dashboard-card-icon{
	width:36px;
	height:36px;
	border-radius:8px;
	display:flex;
	align-items:center;
	justify-content:center;
	background:var(--card-bg,#eef5ff);
	color:var(--card-accent,#4f8df7);
	flex:0 0 auto;
}
.dashboard-card h3{
	margin:0;
	font-size:20px;
	font-weight:700;
	line-height:1.2;
	color:#1f2937;
}
.dashboard-card small{
	color:#6b7280;
	display:block;
	font-size:12px;
	margin-top:3px;
}
.detail-box{
	background:white;
	border:1px solid #e7eaf0;
	border-radius:8px;
	padding:0;
	margin-top:20px;
	box-shadow:0 1px 3px rgba(15,23,42,.08);
	overflow:hidden;
}
.lot-search-card{
	background:white;
	border:1px solid #e7eaf0;
	border-radius:8px;
	padding:16px;
	box-shadow:0 1px 3px rgba(15,23,42,.08);
}
.dashboard-tabs{
	margin-top:20px;
}
.dashboard-tab-list{
	display:flex;
	gap:8px;
	border-bottom:1px solid #dfe4ec;
	margin-bottom:16px;
}
.dashboard-tab-btn{
	border:0;
	background:transparent;
	color:#6b7280;
	padding:10px 14px;
	font-weight:600;
	border-bottom:3px solid transparent;
	cursor:pointer;
}
.dashboard-tab-btn.active{
	color:#1f5eff;
	border-bottom-color:#1f5eff;
}
.dashboard-tab-panel{
	display:none;
}
.dashboard-tab-panel.active{
	display:block;
}
.dashboard-section{
	border-top:1px solid #edf0f4;
}
.dashboard-section:first-child{
	border-top:0;
}
.lot-details-heading, .section-heading{
	display:flex;
	justify-content:space-between;
	align-items:center;
	gap:12px;
	margin-bottom:0;
	padding:16px 20px;
	background:#fbfcfe;
	border-bottom:1px solid #edf0f4;
}
.lot-details-heading h4, .section-heading h4{
	margin:0;
	font-size:16px;
	font-weight:700;
	color:#1f2937;
}
.lot-badge{
	background:#eef6ff;
	color:#1f5eff;
	border-radius:999px;
	padding:4px 10px;
	font-size:12px;
	font-weight:600;
}
.section-title-wrap{
	display:flex;
	align-items:center;
	gap:10px;
	flex-wrap:wrap;
}
.section-toggle{
	border:1px solid #d8dee8;
	background:white;
	color:#4b5563;
	border-radius:6px;
	width:30px;
	height:30px;
	display:flex;
	align-items:center;
	justify-content:center;
	padding:0;
	cursor:pointer;
}
.section-toggle:hover{
	background:#f3f6fb;
	color:#1f2937;
}
.section-toggle .fa{
	transition:transform .15s ease;
}
.section-toggle.is-collapsed .fa{
	transform:rotate(-90deg);
}
.section-body{
	padding:18px 20px 20px;
	overflow-x:auto;
}
.section-body.is-collapsed{
	display:none;
}
.lot-table-wrap{
	overflow-x:auto;
}
.table th{
	background:#f5f5f5;
}
.detail-box .table{
	margin-bottom:0;
}
.detail-box .table th{
	width:16%;
	color:#4b5563;
	font-weight:600;
	white-space:nowrap;
}
.detail-box .alert{
	margin-bottom:0;
}
.detail-box.text-center{
	padding:20px;
}

/* ---- All Lots Table Styles (like child table) ---- */
.all-lots-wrap{
	overflow-x:auto;
}
.all-lots-wrap .table{
	margin-bottom:0;
	white-space:nowrap;
}
.all-lots-wrap .table th{
	position:relative;
	vertical-align:top;
	background:#f5f5f5;
	padding:6px 8px;
	min-width:80px;
}
.all-lots-wrap .table th .col-head{
	font-weight:600;
	color:#4b5563;
	font-size:12px;
	display:block;
	margin-bottom:4px;
}
.all-lots-wrap .table th input.col-filter{
	width:100%;
	box-sizing:border-box;
	padding:3px 6px;
	font-size:11px;
	border:1px solid #d8dee8;
	border-radius:4px;
	outline:none;
	background:white;
	color:#1f2937;
}
.all-lots-wrap .table th input.col-filter:focus{
	border-color:#1f5eff;
	box-shadow:0 0 0 2px rgba(31,94,255,.12);
}
.all-lots-wrap .table td{
	padding:6px 8px;
	font-size:12px;
	color:#1f2937;
}
.all-lots-wrap .table tbody tr:hover{
	background:#f8faff;
}
.all-lots-wrap .lot-count-badge{
	background:#eef6ff;
	color:#1f5eff;
	border-radius:999px;
	padding:4px 10px;
	font-size:12px;
	font-weight:600;
	margin-left:8px;
}

</style>



<div class="tea-dashboard">

<div class="row" id="cards"></div>

<div class="dashboard-tabs">

<div class="dashboard-tab-list">
<button class="dashboard-tab-btn active" data-tab="tea-lot-tab">Tea Lot</button>
<button class="dashboard-tab-btn" data-tab="lot-details-tab">Tea Lot Details</button>
<button class="dashboard-tab-btn" data-tab="mark-tab">Mark</button>
<button class="dashboard-tab-btn" data-tab="grade-tab">Grade</button>
<button class="dashboard-tab-btn" data-tab="evaluation-tab">Tea Evaluation</button>
</div>

<div class="dashboard-tab-panel active" id="tea-lot-tab">
<div id="tea_lot_all"></div>
</div>

<div class="dashboard-tab-panel" id="lot-details-tab">
<div class="lot-search-card">
<div id="lot_search"></div>
<div class="text-muted" style="font-size:12px;margin-top:6px">Search by lot no, mark, grade, seller or invoice number.</div>
</div>
<div id="lot_details"></div>
</div>

<div class="dashboard-tab-panel" id="mark-tab">
<div class="lot-search-card">
<div id="mark_search"></div>
<div class="text-muted" style="font-size:12px;margin-top:6px">Select a mark to view all Tea Lots under that mark.</div>
</div>
<div id="mark_results"></div>
</div>

<div class="dashboard-tab-panel" id="grade-tab">
<div class="lot-search-card">
<div id="grade_search"></div>
<div class="text-muted" style="font-size:12px;margin-top:6px">Select a grade to view all Tea Lots under that grade.</div>
</div>
<div id="grade_results"></div>
</div>

<div class="dashboard-tab-panel" id="evaluation-tab">
<div class="lot-search-card">
<div class="row" style="margin:0;gap:10px;display:flex;flex-wrap:wrap;align-items:end;">
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Colour</label><input type="number" class="form-control" id="eval_colour" placeholder="e.g. 8" step="0.001"></div>
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Strength</label><input type="number" class="form-control" id="eval_strength" placeholder="e.g. 4" step="0.001"></div>
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Taste</label><input type="number" class="form-control" id="eval_taste" placeholder="e.g. 9" step="0.001"></div>
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Briskness</label><input type="number" class="form-control" id="eval_briskness" placeholder="e.g. 10" step="0.001"></div>
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Quality Grade</label>
<select class="form-control" id="eval_quality_grade"><option value="">All</option><option value="A">A</option><option value="A++">A++</option><option value="A+++">A+++</option><option value="B">B</option><option value="B+">B+</option><option value="B++">B++</option><option value="B-">B-</option><option value="C">C</option><option value="C+">C+</option><option value="D">D</option><option value="D+">D+</option><option value="E">E</option><option value="E+">E+</option></select></div>
</div>
<div style="margin:10px 0 0;gap:10px;display:flex;flex-wrap:wrap;align-items:end;">
<div style="flex:1;min-width:180px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Taster</label><div id="eval_taster_field"></div></div>
<div style="flex:1;min-width:120px;"><label style="font-size:12px;font-weight:600;color:#4b5563;display:block;margin-bottom:4px;">Stage</label>
<select class="form-control" id="eval_stage"><option value="">All</option><option value="Pre-purchase">Pre-purchase</option><option value="Arrival">Arrival</option><option value="Blend QC">Blend QC</option><option value="Storage">Storage</option></select></div>
<div style="display:flex;align-items:end;gap:6px;padding-bottom:1px;">
<button class="btn btn-primary btn-sm" id="eval_search_btn"><i class="fa fa-search"></i> Search</button>
<button class="btn btn-default btn-sm" id="eval_clear_btn"><i class="fa fa-eraser"></i> Clear</button></div>
</div>
</div>
<div id="evaluation_results"></div>
</div>

</div>

</div>

`);

	// --------------------------------------------------
	// API CALL
	// --------------------------------------------------

	function api(method, args, callback) {
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_dashboard.tea_lot_dashboard." + method,
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

	function api_from(module, method, args, callback) {
		frappe.call({
			method: "lotwise.lotwise.page.tea_lot_dashboard." + module + "." + method,
			args: args,
			callback: function (r) {
				callback(r.message);
			},
			error: function (r) {
				console.error("API error:", module + "." + method, r);
				callback(null);
			},
		});
	}

	// --------------------------------------------------
	// HELPERS
	// --------------------------------------------------

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function money(value) {
		return "₹ " + fmt(value);
	}

	function vd(value) {
		return value == null || value === "" ? "-" : esc(value);
	}

	function fmt(value) {
		return Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
	}

	// --------------------------------------------------
	// SUMMARY CARDS
	// --------------------------------------------------

	function load_cards() {
		api("get_summary_stats", {}, function (data) {
			let cards = [
				["Total Lots", data.total_lots, "fa-cubes", "#2563eb", "#eff6ff"],
				["Packages", data.total_packages, "fa-archive", "#16a34a", "#f0fdf4"],
				["Net Weight Kg", data.total_net_weight, "fa-balance-scale", "#ea580c", "#fff7ed"],
				["Avg Rate/kg", "₹ " + fmt(data.avg_rate), "fa-inr", "#ca8a04", "#fefce8"],
				["Marks", data.unique_marks, "fa-tags", "#7c3aed", "#f5f3ff"],
				["Grades", data.unique_grades, "fa-signal", "#0891b2", "#ecfeff"],
				["Evaluations", data.total_evaluations, "fa-check-square-o", "#dc2626", "#fef2f2"],
			];
			let html = "";
			cards.forEach(function (c) {
				html += `<div class="col-md" style="flex:1;padding:5px;">
					<div class="dashboard-card" style="--card-accent:${c[3]};--card-bg:${c[4]};">
					<div class="dashboard-card-icon"><i class="fa ${c[2]}"></i></div>
					<div><h3>${c[1] || 0}</h3><small>${c[0]}</small></div>
					</div></div>`;
			});
			$("#cards").html(html);
		});
	}

	// --------------------------------------------------
	// ALL LOTS - FILTERABLE TABLE + MODAL
	// --------------------------------------------------

	var all_lots_data = [];
	var filtered_lots_data = [];
	var filter_timeout = null;
	var current_page = 0;
	var page_size = 10;

	function load_all_lots() {
		$("#tea_lot_all").html(
			`<div class="detail-box text-center text-muted"><i class="fa fa-spinner fa-spin"></i> Loading all tea lots...</div>`
		);
		api_from("tea_lot_dashboard_all_lots", "get_all_lots", {}, function (data) {
			all_lots_data = (data && data.lots) || [];
			current_page = 0;
			render_all_lots_table();
		});
	}

	function render_all_lots_table() {
		var data = all_lots_data;
		if (!data.length) {
			$("#tea_lot_all").html(
				`<div class="detail-box text-center text-muted">No Tea Lots found.</div>`
			);
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

		var filters = {};
		columns.forEach(function (col) {
			var val = $("#flt_" + col.key).val();
			filters[col.key] = (val || "").toLowerCase();
		});

		filtered_lots_data = data.filter(function (row, rowIndex) {
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
		var filtered_with_index = filtered_lots_data.map(function (row, idx) {
			return { row: row, original_index: data.indexOf(row) };
		});

		// Pagination
		var total_pages = Math.ceil(filtered_lots_data.length / page_size);
		if (total_pages === 0) total_pages = 1;
		if (current_page >= total_pages) current_page = total_pages - 1;
		if (current_page < 0) current_page = 0;
		var start_idx = current_page * page_size;
		var page_data = filtered_with_index.slice(start_idx, start_idx + page_size);

		var html = `<div class="detail-box"><div class="section-heading"><div class="section-title-wrap">
			<h4>All Tea Lots</h4>
			<span class="lot-count-badge">${fmt(data.length)} Total</span>
			${
				filtered_lots_data.length !== data.length
					? `<span class="lot-badge" style="background:#fef3c7;color:#92400e;">${fmt(
							filtered_lots_data.length
					  )} Filtered</span>`
					: ""
			}
			<button class="btn btn-default btn-sm" id="download_all_lots_btn" title="Download Excel">
				<i class="fa fa-download"></i> Download
			</button>
		</div></div><div class="section-body" style="padding:0;"><div class="all-lots-wrap">
		<table class="table table-bordered" id="all_lots_table"><thead><tr>`;

		columns.forEach(function (col) {
			var cur_val = filters[col.key] || "";
			html += `<th><span class="col-head">${esc(col.label)}</span>
				<input class="col-filter" id="flt_${col.key}" type="text" value="${esc(
				cur_val
			)}" placeholder="filter" data-col="${col.key}" autocomplete="off" /></th>`;
		});

		html += `</tr></thead><tbody>`;

		if (!page_data.length) {
			html += `<tr><td colspan="${columns.length}" class="text-center text-muted" style="padding:20px;">No matching tea lots found.</td></tr>`;
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
						html +=
							'<td><a href="#" class="lot-detail-link" data-lot="' +
							esc(val) +
							'" style="color:#1f5eff;font-weight:600;text-decoration:none;">' +
							esc(val) +
							"</a></td>";
					} else if (col.numeric) {
						html += "<td>" + (val == null ? "-" : fmt(val)) + "</td>";
					} else if (col.key === "rate") {
						html += "<td>" + money(val) + "</td>";
					} else {
						html += "<td>" + vd(val) + "</td>";
					}
				});
				html += "</tr>";
			});
		}

		// Pagination controls
		var show_start = filtered_lots_data.length ? start_idx + 1 : 0;
		var show_end = Math.min(start_idx + page_size, filtered_lots_data.length);
		var pagination_html = `
			<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-top:1px solid #edf0f4;background:#fbfcfe;">
				<span style="font-size:12px;color:#6b7280;">Showing ${show_start}-${show_end} of ${
			filtered_lots_data.length
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

		html += `</tbody></table></div></div>${pagination_html}</div>`;
		$("#tea_lot_all").html(html);

		$("#tea_lot_all")
			.off("input", ".col-filter")
			.on("input", ".col-filter", function () {
				if (filter_timeout) clearTimeout(filter_timeout);
				filter_timeout = setTimeout(function () {
					current_page = 0;
					render_all_lots_table();
				}, 200);
			});

		$("#tea_lot_all")
			.off("click", "#prev_page_btn")
			.on("click", "#prev_page_btn", function () {
				if (current_page > 0) {
					current_page--;
					render_all_lots_table();
				}
			});
		$("#tea_lot_all")
			.off("click", "#next_page_btn")
			.on("click", "#next_page_btn", function () {
				var total_pages = Math.ceil(filtered_lots_data.length / page_size);
				if (current_page < total_pages - 1) {
					current_page++;
					render_all_lots_table();
				}
			});

		$("#tea_lot_all")
			.off("click", "#download_all_lots_btn")
			.on("click", "#download_all_lots_btn", function (e) {
				e.preventDefault();
				download_all_lots_excel();
			});

		$("#tea_lot_all")
			.off("click", ".lot-detail-link")
			.on("click", ".lot-detail-link", function (e) {
				e.preventDefault();
				show_lot_detail_modal($(this).attr("data-lot"));
			});
	}

	// --------------------------------------------------
	// EXCEL DOWNLOAD - ALL LOTS
	// --------------------------------------------------

	function download_all_lots_excel() {
		if (!filtered_lots_data || !filtered_lots_data.length) {
			frappe.msgprint({
				title: __("No Data"),
				indicator: "orange",
				message: __("No tea lots to download."),
			});
			return;
		}

		var columns = [
			{ key: "name", label: "Tea Lot ID" },
			{ key: "lot_no", label: "Lot No" },
			{ key: "mark", label: "Mark" },
			{ key: "grade", label: "Grade" },
			{ key: "seller", label: "Seller" },
			{ key: "invoice_number", label: "Invoice No" },
			{ key: "liquor_mark", label: "Liquor Mark" },
			{ key: "acquisition_channel", label: "Channel" },
			{ key: "purchase_date", label: "Purchase Date" },
			{ key: "packages", label: "Packages" },
			{ key: "net_weight_total", label: "Net Wt Kg" },
			{ key: "rate", label: "Rate" },
			{ key: "status", label: "Status" },
			{ key: "holding_status", label: "Holding Status" },
			{ key: "warehouse", label: "Warehouse" },
		];

		// Build CSV content
		var csv_content =
			columns
				.map(function (col) {
					return col.label;
				})
				.join(",") + "\n";

		filtered_lots_data.forEach(function (row) {
			var row_data = columns.map(function (col) {
				var val = row[col.key];
				if (val == null) val = "";
				if (col.key === "rate") val = val || 0;
				return val;
			});
			csv_content += row_data.join(",") + "\n";
		});

		// Download
		var date_str = frappe.datetime.now_date();
		var filename = "Tea_Lots_" + date_str + ".csv";

		var blob = new Blob([csv_content], { type: "text/csv" });
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
	}

	// --------------------------------------------------
	// MODAL - TEA LOT DETAILS + EVALUATION
	// --------------------------------------------------

	function show_lot_detail_modal(lot_name) {
		var $modal = $("#lot-detail-modal");
		if (!$modal.length) {
			$("body")
				.append(`<div class="modal fade" id="lot-detail-modal" tabindex="-1" role="dialog">
				<div class="modal-dialog modal-lg" style="width:90%;max-width:1100px;">
				<div class="modal-content">
				<div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><h4 class="modal-title">Tea Lot Details</h4></div>
				<div class="modal-body" style="overflow-x:auto;"><div id="lot-detail-modal-body"><div class="text-center text-muted" style="padding:30px;"><i class="fa fa-spinner fa-spin"></i> Loading...</div></div></div>
				<div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Close</button></div>
				</div></div></div>`);
			$modal = $("#lot-detail-modal");
		}
		$modal.modal("show");
		$("#lot-detail-modal-body").html(
			`<div class="text-center text-muted" style="padding:30px;"><i class="fa fa-spinner fa-spin"></i> Loading tea lot details...</div>`
		);

		api("get_lot_details", { lot_no: lot_name }, function (data) {
			if (!data || !data.lot_details) {
				$("#lot-detail-modal-body").html(
					`<div class="alert alert-info">No Tea Lot details found.</div>`
				);
				return;
			}
			var l = data.lot_details;
			var evals = data.evaluations || [];
			var h = modal_detail_html(l, evals);
			$("#lot-detail-modal-body").html(h);
		});
	}

	function modal_detail_html(l, evals) {
		return `<div style="margin-bottom:20px;">
			<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;background:#fbfcfe;border:1px solid #e7eaf0;border-radius:8px 8px 0 0;border-bottom:0;">
			<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
			<h4 style="margin:0;font-size:16px;font-weight:700;color:#1f2937;">Tea Lot Details</h4>
			<span class="lot-badge">${vd(l.lot_no || l.lot_id)}</span>
			<span class="lot-badge">${vd(l.invoice_number)}</span>
			<span class="lot-badge">${vd(l.mark)}</span></div></div>
			<div style="overflow-x:auto;border:1px solid #e7eaf0;border-radius:0 0 8px 8px;">
			<table class="table table-bordered" style="margin-bottom:0;">
			<tr><th style="width:15%;">Lot ID</th><td style="width:35%;">${vd(
				l.lot_id
			)}</td><th style="width:15%;">Lot No</th><td style="width:35%;">${vd(
			l.lot_no
		)}</td></tr>
			<tr><th>Mark</th><td>${vd(l.mark)}</td><th>Grade</th><td>${vd(l.grade)}</td></tr>
			<tr><th>Seller</th><td>${vd(l.seller)}</td><th>Invoice Number</th><td>${vd(
			l.invoice_number
		)}</td></tr>
			<tr><th>Channel</th><td>${vd(l.acquisition_channel)}</td><th>Status</th><td>${vd(
			l.status
		)}</td></tr>
			<tr><th>Holding Status</th><td>${vd(l.holding_status)}</td><th>Intended Segment</th><td>${vd(
			l.intended_segment
		)}</td></tr>
			<tr><th>Packages</th><td>${fmt(l.packages)}</td><th>Net Weight</th><td>${fmt(
			l.net_weight_total
		)} Kg</td></tr>
			<tr><th>Gross Wt/Pkg</th><td>${fmt(l.gross_wtpkg)} Kg</td><th>Net Wt/Pkg</th><td>${fmt(
			l.net_wtpkg
		)} Kg</td></tr>
			<tr><th>Rate</th><td>${money(l.rate)}</td><th>Density</th><td>${fmt(l.density)}</td></tr>
			<tr><th>Packing</th><td>${vd(l.packing)}</td><th>Liquor Mark</th><td>${vd(l.liquor_mark)}</td></tr>
			<tr><th>Blend</th><td>${vd(l.blend)}</td><th>Warehouse</th><td>${vd(l.warehouse)}</td></tr>
			<tr><th>Purchase Date</th><td>${vd(l.purchase_date)}</td><th>GP No</th><td>${vd(l.gp_no)}</td></tr>
			<tr><th>GP Date</th><td>${vd(l.gp_date)}</td><th>AWR Date</th><td>${vd(l.awr_date)}</td></tr>
			<tr><th>Broker</th><td>${vd(l.broker)}</td><th>Sale No</th><td>${vd(l.sale_no)}</td></tr>
			<tr><th>Centre</th><td>${vd(l.centre)}</td><th>Division</th><td>${vd(l.division)}</td></tr>
			<tr><th>Manufacturer Ref</th><td>${vd(l.manufacturer_ref)}</td><th>Chest Serial Range</th><td>${vd(
			l.chest_serial_range
		)}</td></tr>
			<tr><th>Certification</th><td>${vd(l.certification)}</td><th>Mfg Month/Year</th><td>${vd(
			l.mfg_monthyear
		)}</td></tr>
			<tr><th>DO Reference</th><td>${vd(l.do_reference)}</td><th>DO Date</th><td>${vd(
			l.do_date
		)}</td></tr>
			<tr><th>Source Doctype</th><td>${vd(l.source_doctype)}</td><th>Source ID</th><td>${vd(
			l.source_doctype_id
		)}</td></tr>
			</table></div></div>
			<div style="border:1px solid #e7eaf0;border-radius:8px;overflow:hidden;">
			<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;background:#fbfcfe;border-bottom:1px solid #edf0f4;">
			<div style="display:flex;align-items:center;gap:10px;"><h4 style="margin:0;font-size:16px;font-weight:700;color:#1f2937;">Tea Evaluation</h4>
			<span class="lot-badge">${fmt(evals.length)}</span></div></div>
			<div style="overflow-x:auto;">${modal_eval_table(evals)}</div></div>`;
	}

	function modal_eval_table(data) {
		if (!data || !data.length)
			return `<div class="alert alert-info" style="margin:0;border-radius:0;">No Evaluation Found</div>`;
		var h = `<table class="table table-bordered" style="margin-bottom:0;"><tr><th>Taster</th><th>Stage</th><th>Date</th><th>Colour</th><th>Strength</th><th>Taste</th><th>Briskness</th><th>Quality</th><th>Suggested Value</th><th>Notes</th></tr>`;
		data.forEach(function (e) {
			h += `<tr><td>${vd(e.taster)}</td><td>${vd(e.stage)}</td><td>${vd(
				e.evaluation_date
			)}</td><td>${fmt(e.colour)}</td><td>${fmt(e.strength)}</td><td>${fmt(
				e.taste
			)}</td><td>${fmt(e.briskness)}</td><td>${vd(e.quality_grade)}</td><td>${money(
				e.suggested_valuation
			)}</td><td>${vd(e.notes)}</td></tr>`;
		});
		return h + "</table>";
	}

	// --------------------------------------------------
	// MARK TAB
	// --------------------------------------------------

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

	function load_mark_lots(mark) {
		$("#mark_results").html(
			`<div class="detail-box text-center text-muted"><i class="fa fa-spinner fa-spin"></i> Loading tea lots for this mark...</div>`
		);
		api_from("tea_lot_dashboard_mark", "get_lots_by_mark", { mark: mark }, function (data) {
			var lots = (data && data.lots) || [];
			$("#mark_results").html(mark_lot_table(mark, lots));

			$("#mark_results")
				.off("click", "#download_mark_btn")
				.on("click", "#download_mark_btn", function () {
					download_mark_excel(mark, lots);
				});
		});
	}

	function mark_lot_table(mark, lots) {
		if (!lots.length)
			return `<div class="detail-box text-center text-muted">No Tea Lots found for mark ${vd(
				mark
			)}.</div>`;
		var h = `<div class="detail-box"><div class="section-heading"><div class="section-title-wrap"><h4>Tea Lots By Mark</h4><span class="lot-badge">${vd(
			mark
		)}</span><span class="lot-badge">${fmt(lots.length)} Lots</span>
		<button class="btn btn-default btn-sm" id="download_mark_btn" title="Download Excel">
			<i class="fa fa-download"></i> Download
		</button></div></div><div class="section-body"><table class="table table-bordered"><tr><th>Lot No</th><th>Tea Lot ID</th><th>Grade</th><th>Invoice Number</th><th>Liquor Mark</th><th>Acquisition Channel</th><th>Purchase Date</th><th>Packages</th><th>Net Weight Kg</th><th>Rate</th><th>Status</th><th>Holding Status</th></tr>`;
		lots.forEach(function (lot) {
			h += `<tr><td>${vd(lot.lot_no || lot.name)}</td><td>${vd(lot.name)}</td><td>${vd(
				lot.grade
			)}</td><td>${vd(lot.invoice_number)}</td><td>${vd(lot.liquor_mark)}</td><td>${vd(
				lot.acquisition_channel
			)}</td><td>${vd(lot.purchase_date)}</td><td>${fmt(lot.packages)}</td><td>${fmt(
				lot.net_weight_total
			)}</td><td>${money(lot.rate)}</td><td>${vd(lot.status)}</td><td>${vd(
				lot.holding_status
			)}</td></tr>`;
		});
		return h + `</table></div></div>`;
	}

	// --------------------------------------------------
	// EXCEL DOWNLOAD - MARK
	// --------------------------------------------------

	function download_mark_excel(mark, lots) {
		if (!lots.length) {
			frappe.msgprint({
				title: __("No Data"),
				indicator: "orange",
				message: __("No tea lots to download."),
			});
			return;
		}

		var columns = [
			{ key: "lot_no", label: "Lot No" },
			{ key: "name", label: "Tea Lot ID" },
			{ key: "grade", label: "Grade" },
			{ key: "invoice_number", label: "Invoice Number" },
			{ key: "liquor_mark", label: "Liquor Mark" },
			{ key: "acquisition_channel", label: "Acquisition Channel" },
			{ key: "purchase_date", label: "Purchase Date" },
			{ key: "packages", label: "Packages" },
			{ key: "net_weight_total", label: "Net Weight Kg" },
			{ key: "rate", label: "Rate" },
			{ key: "status", label: "Status" },
			{ key: "holding_status", label: "Holding Status" },
		];

		// Build CSV content
		var csv_content =
			columns
				.map(function (col) {
					return col.label;
				})
				.join(",") + "\n";

		lots.forEach(function (row) {
			var row_data = columns.map(function (col) {
				var val = row[col.key];
				if (val == null) val = "";
				if (col.key === "rate") val = val || 0;
				return val;
			});
			csv_content += row_data.join(",") + "\n";
		});

		// Download
		var date_str = frappe.datetime.now_date();
		var filename = "Tea_Lots_Mark_" + (mark || "All") + "_" + date_str + ".csv";

		var blob = new Blob([csv_content], { type: "text/csv" });
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
	}

	// --------------------------------------------------
	// GRADE TAB
	// --------------------------------------------------

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

	function load_grade_lots(grade) {
		$("#grade_results").html(
			`<div class="detail-box text-center text-muted"><i class="fa fa-spinner fa-spin"></i> Loading tea lots for this grade...</div>`
		);
		api_from(
			"tea_lot_dashboard_grade",
			"get_lots_by_grade",
			{ grade: grade },
			function (data) {
				var lots = (data && data.lots) || [];
				$("#grade_results").html(grade_lot_table(grade, lots));

				$("#grade_results")
					.off("click", "#download_grade_btn")
					.on("click", "#download_grade_btn", function () {
						download_grade_excel(grade, lots);
					});
			}
		);
	}

	function grade_lot_table(grade, lots) {
		if (!lots.length)
			return `<div class="detail-box text-center text-muted">No Tea Lots found for grade ${vd(
				grade
			)}.</div>`;
		var h = `<div class="detail-box"><div class="section-heading"><div class="section-title-wrap"><h4>Tea Lots By Grade</h4><span class="lot-badge">${vd(
			grade
		)}</span><span class="lot-badge">${fmt(lots.length)} Lots</span>
		<button class="btn btn-default btn-sm" id="download_grade_btn" title="Download Excel">
			<i class="fa fa-download"></i> Download
		</button></div></div><div class="section-body"><table class="table table-bordered"><tr><th>Lot No</th><th>Tea Lot ID</th><th>Mark</th><th>Invoice Number</th><th>Liquor Mark</th><th>Acquisition Channel</th><th>Purchase Date</th><th>Packages</th><th>Net Weight Kg</th><th>Rate</th><th>Status</th><th>Holding Status</th></tr>`;
		lots.forEach(function (lot) {
			h += `<tr><td>${vd(lot.lot_no || lot.name)}</td><td>${vd(lot.name)}</td><td>${vd(
				lot.mark
			)}</td><td>${vd(lot.invoice_number)}</td><td>${vd(lot.liquor_mark)}</td><td>${vd(
				lot.acquisition_channel
			)}</td><td>${vd(lot.purchase_date)}</td><td>${fmt(lot.packages)}</td><td>${fmt(
				lot.net_weight_total
			)}</td><td>${money(lot.rate)}</td><td>${vd(lot.status)}</td><td>${vd(
				lot.holding_status
			)}</td></tr>`;
		});
		return h + `</table></div></div>`;
	}

	// --------------------------------------------------
	// EXCEL DOWNLOAD - GRADE
	// --------------------------------------------------

	function download_grade_excel(grade, lots) {
		if (!lots.length) {
			frappe.msgprint({
				title: __("No Data"),
				indicator: "orange",
				message: __("No tea lots to download."),
			});
			return;
		}

		var columns = [
			{ key: "lot_no", label: "Lot No" },
			{ key: "name", label: "Tea Lot ID" },
			{ key: "mark", label: "Mark" },
			{ key: "invoice_number", label: "Invoice Number" },
			{ key: "liquor_mark", label: "Liquor Mark" },
			{ key: "acquisition_channel", label: "Acquisition Channel" },
			{ key: "purchase_date", label: "Purchase Date" },
			{ key: "packages", label: "Packages" },
			{ key: "net_weight_total", label: "Net Weight Kg" },
			{ key: "rate", label: "Rate" },
			{ key: "status", label: "Status" },
			{ key: "holding_status", label: "Holding Status" },
		];

		// Build CSV content
		var csv_content =
			columns
				.map(function (col) {
					return col.label;
				})
				.join(",") + "\n";

		lots.forEach(function (row) {
			var row_data = columns.map(function (col) {
				var val = row[col.key];
				if (val == null) val = "";
				if (col.key === "rate") val = val || 0;
				return val;
			});
			csv_content += row_data.join(",") + "\n";
		});

		// Download
		var date_str = frappe.datetime.now_date();
		var filename = "Tea_Lots_Grade_" + (grade || "All") + "_" + date_str + ".csv";

		var blob = new Blob([csv_content], { type: "text/csv" });
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
	}

	// --------------------------------------------------
	// EVALUATION TAB
	// --------------------------------------------------

	var taster_field = null;

	function create_evaluation_search() {
		$("#eval_search_btn").on("click", function () {
			load_evaluations();
		});
		$("#eval_clear_btn").on("click", function () {
			$(
				"#eval_colour,#eval_strength,#eval_taste,#eval_briskness,#eval_quality_grade,#eval_stage"
			).val("");
			if (taster_field) taster_field.set_value("");
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
					load_evaluations();
				},
			},
			render_input: true,
		});
		taster_field.refresh();
	}

	function load_evaluations() {
		var args = {};
		var colour = $("#eval_colour").val().trim();
		var strength = $("#eval_strength").val().trim();
		var taste = $("#eval_taste").val().trim();
		var briskness = $("#eval_briskness").val().trim();
		var quality_grade = $("#eval_quality_grade").val();
		var stage = $("#eval_stage").val();
		var taster_val = taster_field ? (taster_field.get_value() || "").trim() : "";
		if (colour) args.colour = colour;
		if (strength) args.strength = strength;
		if (taste) args.taste = taste;
		if (briskness) args.briskness = briskness;
		if (quality_grade) args.quality_grade = quality_grade;
		if (taster_val) args.taster = taster_val;
		if (stage) args.stage = stage;

		$("#evaluation_results").html(
			`<div class="detail-box text-center text-muted"><i class="fa fa-spinner fa-spin"></i> Loading evaluations...</div>`
		);
		api_from("tea_lot_dashboard_evaluation", "get_evaluations", args, function (data) {
			var evals = (data && data.evaluations) || [];
			$("#evaluation_results").html(eval_table(evals));

			$("#evaluation_results")
				.off("click", "#download_eval_btn")
				.on("click", "#download_eval_btn", function () {
					download_evaluation_excel(evals);
				});
		});
	}

	function eval_table(evals) {
		if (!evals.length)
			return `<div class="detail-box text-center text-muted">No Evaluations found.</div>`;
		var h = `<div class="detail-box"><div class="section-heading"><div class="section-title-wrap"><h4>Tea Evaluation Results</h4><span class="lot-badge">${fmt(
			evals.length
		)} Records</span>
		<button class="btn btn-default btn-sm" id="download_eval_btn" title="Download Excel">
			<i class="fa fa-download"></i> Download
		</button></div></div><div class="section-body" style="overflow-x:auto;"><table class="table table-bordered"><tr><th>Tea Evaluation ID</th><th>Tea Lot</th><th>Lot No</th><th>Mark</th><th>Colour</th><th>Strength</th><th>Taste</th><th>Briskness</th><th>Quality Grade</th><th>Taster</th><th>Stage</th><th>Eval Date</th><th>Suggested Valuation</th><th>Notes</th></tr>`;
		evals.forEach(function (e) {
			h += `<tr><td>${vd(e.name)}</td><td>${vd(e.tea_lot)}</td><td>${vd(
				e.tea_lot_no
			)}</td><td>${vd(e.tea_lot_mark)}</td><td>${fmt(e.colour)}</td><td>${fmt(
				e.strength
			)}</td><td>${fmt(e.taste)}</td><td>${fmt(e.briskness)}</td><td>${vd(
				e.quality_grade
			)}</td><td>${vd(e.taster)}</td><td>${vd(e.stage)}</td><td>${vd(
				e.evaluation_date
			)}</td><td>${money(e.suggested_valuation)}</td><td>${vd(e.notes)}</td></tr>`;
		});
		return h + `</table></div></div>`;
	}

	// --------------------------------------------------
	// EXCEL DOWNLOAD - EVALUATION
	// --------------------------------------------------

	function download_evaluation_excel(evals) {
		if (!evals.length) {
			frappe.msgprint({
				title: __("No Data"),
				indicator: "orange",
				message: __("No evaluations to download."),
			});
			return;
		}

		var columns = [
			{ key: "name", label: "Tea Evaluation ID" },
			{ key: "tea_lot", label: "Tea Lot" },
			{ key: "tea_lot_no", label: "Lot No" },
			{ key: "tea_lot_mark", label: "Mark" },
			{ key: "colour", label: "Colour" },
			{ key: "strength", label: "Strength" },
			{ key: "taste", label: "Taste" },
			{ key: "briskness", label: "Briskness" },
			{ key: "quality_grade", label: "Quality Grade" },
			{ key: "taster", label: "Taster" },
			{ key: "stage", label: "Stage" },
			{ key: "evaluation_date", label: "Eval Date" },
			{ key: "suggested_valuation", label: "Suggested Valuation" },
			{ key: "notes", label: "Notes" },
		];

		// Build CSV content
		var csv_content =
			columns
				.map(function (col) {
					return col.label;
				})
				.join(",") + "\n";

		evals.forEach(function (row) {
			var row_data = columns.map(function (col) {
				var val = row[col.key];
				if (val == null) val = "";
				if (col.key === "suggested_valuation") val = val || 0;
				return val;
			});
			csv_content += row_data.join(",") + "\n";
		});

		// Download
		var date_str = frappe.datetime.now_date();
		var filename = "Tea_Evaluations_" + date_str + ".csv";

		var blob = new Blob([csv_content], { type: "text/csv" });
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
	}

	// --------------------------------------------------
	// TEA LOT DETAILS TAB
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

	function load_lot_details(lot) {
		$("#lot_details").html(
			`<div class="detail-box text-center text-muted"><i class="fa fa-spinner fa-spin"></i> Loading tea lot details...</div>`
		);
		api("get_lot_details", { lot_no: lot }, function (data) {
			if (!data || !data.lot_details) {
				$("#lot_details").html(
					`<div class="detail-box text-center text-muted">No Tea Lot found.</div>`
				);
				return;
			}
			var l = data.lot_details;
			var evals = data.evaluations || [];
			var h = `<div class="detail-box"><div class="lot-details-heading"><div class="section-title-wrap"><h4>Tea Lot Details</h4>
				<span class="lot-badge">${vd(l.lot_no || l.lot_id)}</span>
				<span class="lot-badge">${vd(l.invoice_number)}</span>
				<span class="lot-badge">${vd(l.mark)}</span></div>
				<button class="section-toggle" data-target="#tea-lot-info-section" aria-expanded="true" title="Collapse Tea Lot Details"><i class="fa fa-chevron-down"></i></button></div>
				<div class="section-body" id="tea-lot-info-section"><div class="lot-table-wrap">
				<table class="table table-bordered">
				<tr><th>Lot ID</th><td>${vd(l.lot_id)}</td><th>Lot No</th><td>${vd(l.lot_no)}</td></tr>
				<tr><th>Mark</th><td>${vd(l.mark)}</td><th>Grade</th><td>${vd(l.grade)}</td></tr>
				<tr><th>Seller</th><td>${vd(l.seller)}</td><th>Invoice Number</th><td>${vd(
				l.invoice_number
			)}</td></tr>
				<tr><th>Channel</th><td>${vd(l.acquisition_channel)}</td><th>Status</th><td>${vd(
				l.status
			)}</td></tr>
				<tr><th>Holding Status</th><td>${vd(l.holding_status)}</td><th>Intended Segment</th><td>${vd(
				l.intended_segment
			)}</td></tr>
				<tr><th>Packages</th><td>${fmt(l.packages)}</td><th>Net Weight</th><td>${fmt(
				l.net_weight_total
			)} Kg</td></tr>
				<tr><th>Gross Wt/Pkg</th><td>${fmt(l.gross_wtpkg)} Kg</td><th>Net Wt/Pkg</th><td>${fmt(
				l.net_wtpkg
			)} Kg</td></tr>
				<tr><th>Rate</th><td>${money(l.rate)}</td><th>Density</th><td>${fmt(l.density)}</td></tr>
				<tr><th>Packing</th><td>${vd(l.packing)}</td><th>Liquor Mark</th><td>${vd(l.liquor_mark)}</td></tr>
				<tr><th>Blend</th><td>${vd(l.blend)}</td><th>Warehouse</th><td>${vd(l.warehouse)}</td></tr>
				<tr><th>Purchase Date</th><td>${vd(l.purchase_date)}</td><th>GP No</th><td>${vd(l.gp_no)}</td></tr>
				<tr><th>GP Date</th><td>${vd(l.gp_date)}</td><th>AWR Date</th><td>${vd(l.awr_date)}</td></tr>
				<tr><th>Broker</th><td>${vd(l.broker)}</td><th>Sale No</th><td>${vd(l.sale_no)}</td></tr>
				<tr><th>Centre</th><td>${vd(l.centre)}</td><th>Division</th><td>${vd(l.division)}</td></tr>
				<tr><th>Manufacturer Ref</th><td>${vd(l.manufacturer_ref)}</td><th>Chest Serial Range</th><td>${vd(
				l.chest_serial_range
			)}</td></tr>
				<tr><th>Certification</th><td>${vd(l.certification)}</td><th>Mfg Month/Year</th><td>${vd(
				l.mfg_monthyear
			)}</td></tr>
				<tr><th>DO Reference</th><td>${vd(l.do_reference)}</td><th>DO Date</th><td>${vd(
				l.do_date
			)}</td></tr>
				<tr><th>Source Doctype</th><td>${vd(l.source_doctype)}</td><th>Source ID</th><td>${vd(
				l.source_doctype_id
			)}</td></tr>
				</table></div></div>
				<div class="dashboard-section"><div class="section-heading"><div class="section-title-wrap"><h4>Tea Evaluation</h4><span class="lot-badge">${fmt(
					evals.length
				)}</span></div>
				<button class="section-toggle" data-target="#tea-evaluation-section" aria-expanded="true" title="Collapse Tea Evaluation"><i class="fa fa-chevron-down"></i></button></div>
				<div class="section-body" id="tea-evaluation-section">${lot_detail_eval_table(
					evals
				)}</div></div></div>`;
			$("#lot_details").html(h);
		});
	}

	function lot_detail_eval_table(data) {
		if (!data || !data.length)
			return `<div class="alert alert-info">No Evaluation Found</div>`;
		var h = `<table class="table table-bordered"><tr><th>Taster</th><th>Stage</th><th>Date</th><th>Colour</th><th>Strength</th><th>Taste</th><th>Briskness</th><th>Quality</th><th>Suggested Value</th><th>Notes</th></tr>`;
		data.forEach(function (e) {
			h += `<tr><td>${vd(e.taster)}</td><td>${vd(e.stage)}</td><td>${vd(
				e.evaluation_date
			)}</td><td>${fmt(e.colour)}</td><td>${fmt(e.strength)}</td><td>${fmt(
				e.taste
			)}</td><td>${fmt(e.briskness)}</td><td>${vd(e.quality_grade)}</td><td>${money(
				e.suggested_valuation
			)}</td><td>${vd(e.notes)}</td></tr>`;
		});
		return h + "</table>";
	}

	// --------------------------------------------------
	// TAB CLICK HANDLER
	// --------------------------------------------------

	$(page.main).on("click", ".dashboard-tab-btn", function () {
		let tab = $(this).attr("data-tab");
		$(".dashboard-tab-btn").removeClass("active");
		$(this).addClass("active");
		$(".dashboard-tab-panel").removeClass("active");
		$("#" + tab).addClass("active");
		if (tab === "tea-lot-tab") {
			load_all_lots();
		} else if (tab === "evaluation-tab") {
			load_evaluations();
		}
	});

	$(page.main).on("click", ".section-toggle", function () {
		let $btn = $(this);
		let target = $btn.attr("data-target");
		let $body = $(target);
		let collapsed = !$body.hasClass("is-collapsed");
		$body.toggleClass("is-collapsed", collapsed);
		$btn.toggleClass("is-collapsed", collapsed);
		$btn.attr("aria-expanded", collapsed ? "false" : "true");
	});

	// --------------------------------------------------
	// INIT
	// --------------------------------------------------

	load_cards();
	load_all_lots();
	create_lot_search();
	create_mark_search();
	create_grade_search();
	create_evaluation_search();
};
