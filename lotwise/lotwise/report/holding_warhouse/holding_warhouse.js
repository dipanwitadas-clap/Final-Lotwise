// Copyright (c) 2026, BusinessThat.Works

const BADGE_STYLES = {
	holding_status: {
		Committed: ["#dcfce7", "#166534"],
		Received: ["#dbeafe", "#1e40af"],
		"In Stock": ["#fef3c7", "#92400e"],
	},
	status: {
		Offered: ["#f3e8ff", "#6b21a8"],
		Evaluated: ["#fce7f3", "#9d174d"],
	},
	acquisition_channel: {
		Auction: ["#e0e7ff", "#3730a3"],
		Private: ["#fef3c7", "#92400e"],
		Outsourced: ["#e0f2fe", "#075985"],
	},
};

const NUMERIC_COLUMNS = new Set(["packages", "net_weight_total", "rate"]);
const CENTER_COLUMNS = new Set([
	"acquisition_channel",
	"status",
	"holding_status",
	"purchase_date",
]);

function badge(value, colors) {
	const [background, color] = colors;

	return `<span class="holding-warehouse-badge" style="background:${background};color:${color};">${value}</span>`;
}

frappe.query_reports["Holding Warhouse"] = {
	filters: [
		{
			fieldname: "name",
			label: __("Lot ID"),
			fieldtype: "Link",
			options: "Tea Lot",
		},
		{
			fieldname: "acquisition_channel",
			label: __("Acquisition Channel"),
			fieldtype: "Select",
			options: "\nAuction\nPrivate\nOutsourced",
		},
		{
			fieldname: "lot_no",
			label: __("Lot No"),
			fieldtype: "Data",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "holding_status",
			label: __("Holding Status"),
			fieldtype: "Select",
			options: "\nCommitted\nReceived\nIn Stock",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOffered\nEvaluated",
		},
		{
			fieldname: "mark",
			label: __("Mark"),
			fieldtype: "Link",
			options: "Mark",
		},
		{
			fieldname: "grade",
			label: __("Grade"),
			fieldtype: "Link",
			options: "Grade",
		},
		{
			fieldname: "auction_centre",
			label: __("Auction Centre"),
			fieldtype: "Link",
			options: "Auction Centre",
		},
		{
			fieldname: "sale_no_from",
			label: __("Sale No From"),
			fieldtype: "Int",
		},

		{
			fieldname: "sale_no_to",
			label: __("Sale No To"),
			fieldtype: "Int",
		},
	],

	onload(report) {
		$(report.page.main).addClass("holding-warehouse-report");

		if (document.getElementById("holding-warehouse-report-style")) {
			return;
		}

		const style = document.createElement("style");
		style.id = "holding-warehouse-report-style";
		style.textContent = `
			.holding-warehouse-report .dt-cell__content {
				align-items: center;
				display: flex;
				min-height: 34px;
				overflow: hidden;
				padding: 7px 10px !important;
				text-overflow: ellipsis;
				white-space: nowrap;
			}

			.holding-warehouse-report .dt-row-header .dt-cell__content {
				color: var(--text-muted);
				font-size: 12px;
				font-weight: 600;
				letter-spacing: 0;
			}

			.holding-warehouse-report .dt-row:not(.dt-row-header):hover {
				background: var(--bg-light-gray);
			}

			.holding-warehouse-cell {
				display: block;
				overflow: hidden;
				text-overflow: ellipsis;
				width: 100%;
			}

			.holding-warehouse-cell.text-right {
				text-align: right;
			}

			.holding-warehouse-cell.text-center {
				text-align: center;
			}

			.holding-warehouse-badge {
				border-radius: 999px;
				display: inline-flex;
				font-size: 12px;
				font-weight: 600;
				justify-content: center;
				line-height: 1.2;
				min-width: 72px;
				padding: 4px 9px;
				vertical-align: middle;
			}
		`;
		document.head.appendChild(style);
	},

	formatter(value, row, column, data, default_formatter) {
		const formatted_value = default_formatter(value, row, column, data);
		const fieldname = column.fieldname;
		const field_styles = BADGE_STYLES[fieldname] || {};
		const badge_colors = field_styles[data && data[fieldname]];
		const content = badge_colors ? badge(formatted_value, badge_colors) : formatted_value;

		if (NUMERIC_COLUMNS.has(fieldname)) {
			return `<span class="holding-warehouse-cell text-right">${content}</span>`;
		}

		if (CENTER_COLUMNS.has(fieldname)) {
			return `<span class="holding-warehouse-cell text-center">${content}</span>`;
		}

		return `<span class="holding-warehouse-cell">${content}</span>`;
	},
};
