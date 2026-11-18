// Copyright (c) 2026, BusinessThat.Works

const BADGE_STYLES = {
	purchase_status: {
		Committed: ["#dcfce7", "#166534"],
		Received: ["#dbeafe", "#1e40af"],
		"In Stock": ["#fef3c7", "#92400e"],
	},
	acquisition_channel: {
		Auction: ["#e0e7ff", "#3730a3"],
		Private: ["#fef3c7", "#92400e"],
		Outsourced: ["#e0f2fe", "#075985"],
	},
};

const NUMERIC_COLUMNS = new Set(["packages", "net_weight_total", "rate", "total_amount"]);
const CENTER_COLUMNS = new Set(["acquisition_channel", "purchase_status"]);

function badge(value, colors) {
	const [background, color] = colors;

	return `<span class="holding-warehouse-badge" style="background:${background};color:${color};">${value}</span>`;
}

frappe.query_reports["Holding Warhouse"] = {
	filters: [
		{
			fieldname: "name",
			label: __("Tea Lot"),
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
			fieldname: "purchase_status",
			label: __("Purchase Status"),
			fieldtype: "Link",
			options: "Purchase Status",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
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

		let style = document.getElementById("holding-warehouse-report-style");
		if (!style) {
			style = document.createElement("style");
			style.id = "holding-warehouse-report-style";
			document.head.appendChild(style);
		}

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

			.holding-warehouse-report .dt-row-footer .dt-cell__content {
				font-weight: 700;
			}
		`;
	},

	refresh(report) {
		if (!report.data) return;

		setTimeout(() => {
			const tableBody = report.pages[0]?.querySelector(".dt-table tbody");
			if (!tableBody) return;

			const rows = tableBody.querySelectorAll("tr");
			rows.forEach((row, index) => {
				const rowData = report.data[index];
				if (rowData && rowData.name === "Total") {
					const cells = row.querySelectorAll("td");
					cells.forEach((cell) => {
						const content = cell.querySelector(".dt-cell__content");
						if (content) {
							content.style.fontWeight = "700";
							content.style.color = "black";
							const badge = content.querySelector(".holding-warehouse-badge");
							if (badge) {
								badge.style.background = "transparent";
								badge.style.color = "black";
								badge.style.fontWeight = "700";
							}
						}
					});
				}
			});
		}, 50);
	},

	formatter(value, row, column, data, default_formatter) {
		const formatted_value = default_formatter(value, row, column, data);
		const fieldname = column.fieldname;
		const is_total_row = data && data.name === "Total";
		const field_styles = BADGE_STYLES[fieldname] || {};
		const badge_colors = is_total_row ? null : field_styles[data && data[fieldname]];
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
