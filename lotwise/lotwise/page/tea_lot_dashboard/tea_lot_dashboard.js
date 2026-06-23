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

	box-shadow:
	0 1px 3px rgba(15,23,42,.08);

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

	box-shadow:
	0 1px 3px rgba(15,23,42,.08);

	overflow:hidden;

}



.lot-search-card{

	background:white;

	border:1px solid #e7eaf0;

	border-radius:8px;

	padding:16px;

	box-shadow:
	0 1px 3px rgba(15,23,42,.08);

}



.dashboard-section{

	border-top:1px solid #edf0f4;

}



.dashboard-section:first-child{

	border-top:0;

}



.lot-details-heading,
.section-heading{

	display:flex;

	justify-content:space-between;

	align-items:center;

	gap:12px;

	margin-bottom:0;

	padding:16px 20px;

	background:#fbfcfe;

	border-bottom:1px solid #edf0f4;

}



.lot-details-heading h4,
.section-heading h4{

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
				["Total Lots", data.total_lots, "fa-cubes", "#2563eb", "#eff6ff"],

				["Packages", data.total_packages, "fa-archive", "#16a34a", "#f0fdf4"],

				["Net Weight Kg", data.total_net_weight, "fa-balance-scale", "#ea580c", "#fff7ed"],

				["Total Rate", "₹ " + format(data.total_rate), "fa-inr", "#ca8a04", "#fefce8"],

				["Marks", data.unique_marks, "fa-tags", "#7c3aed", "#f5f3ff"],

				["Grades", data.unique_grades, "fa-signal", "#0891b2", "#ecfeff"],

				["Evaluations", data.total_evaluations, "fa-check-square-o", "#dc2626", "#fef2f2"],
			];

			let html = "";

			cards.forEach(function (c) {
				html += `


					<div class="col-md"
					style="
					flex:1;
					padding:5px;
					">


					<div class="dashboard-card"
					style="--card-accent:${c[3]};--card-bg:${c[4]};">


					<div class="dashboard-card-icon">
					<i class="fa ${c[2]}"></i>
					</div>


					<div>


					<h3>
					${c[1] || 0}
					</h3>


					<small>
					${c[0]}
					</small>


					</div>

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

	$(page.main).on("click", ".section-toggle", function () {
		let $button = $(this);
		let target = $button.attr("data-target");
		let $body = $(target);
		let collapsed = !$body.hasClass("is-collapsed");

		$body.toggleClass("is-collapsed", collapsed);
		$button.toggleClass("is-collapsed", collapsed);
		$button.attr("aria-expanded", collapsed ? "false" : "true");
	});

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
<div class="section-title-wrap">
<h4>Tea Lot Details</h4>
<span class="lot-badge">${value_or_dash(l.lot_no || l.lot_id)}</span>
</div>
<button class="section-toggle" data-target="#tea-lot-info-section" aria-expanded="true" title="Collapse Tea Lot Details">
<i class="fa fa-chevron-down"></i>
</button>
</div>

<div class="section-body" id="tea-lot-info-section">

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

</div>

<div class="dashboard-section">
<div class="section-heading">
<div class="section-title-wrap">
<h4>
Tea Evaluation
</h4>
<span class="lot-badge">${format((data.evaluations || []).length)}</span>
</div>
<button class="section-toggle" data-target="#tea-evaluation-section" aria-expanded="true" title="Collapse Tea Evaluation">
<i class="fa fa-chevron-down"></i>
</button>
</div>

<div class="section-body" id="tea-evaluation-section">


${evaluation_table(data.evaluations)}


</div>
</div>


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
