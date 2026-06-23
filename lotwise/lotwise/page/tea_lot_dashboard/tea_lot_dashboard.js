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

				["Total Rate", "₹ " + format(data.total_rate)],

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
