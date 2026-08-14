// Copyright (c) 2026, BusinessThat.Works

frappe.query_reports["Tea Evaluation Comparison"] = {
	filters: [
		{
			fieldname: "tea_lot",
			label: __("Tea Lot"),
			fieldtype: "Link",
			options: "Tea Lot",
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
			fieldname: "taster",
			label: __("Taster"),
			fieldtype: "Link",
			options: "Taster",
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
	],

	onload(report) {
		$(report.page.main).addClass("tea-eval-comparison-report");

		let style = document.getElementById("tea-eval-comparison-report-style");
		if (!style) {
			style = document.createElement("style");
			style.id = "tea-eval-comparison-report-style";
			document.head.appendChild(style);
		}

		style.textContent = `
			.tea-eval-comparison-report .dt-cell__content {
				align-items: center;
				display: flex;
				min-height: 34px;
				overflow: hidden;
				padding: 7px 10px !important;
				text-overflow: ellipsis;
				white-space: nowrap;
			}

			.tea-eval-comparison-report .dt-row-header .dt-cell__content {
				color: var(--text-muted);
				font-size: 12px;
				font-weight: 600;
				letter-spacing: 0;
			}

			.tea-eval-comparison-report .dt-row:not(.dt-row-header):hover {
				background: var(--bg-light-gray);
			}

			.tea-eval-comparison-cell {
				display: block;
				overflow: hidden;
				text-overflow: ellipsis;
				width: 100%;
			}

			.tea-eval-comparison-diff {
				border-radius: 999px;
				display: inline-flex;
				font-size: 12px;
				font-weight: 700;
				justify-content: center;
				line-height: 1.2;
				min-width: 40px;
				padding: 3px 8px;
				vertical-align: middle;
			}

			.tea-eval-comparison-diff.positive {
				background: #dcfce7;
				color: #166534;
			}

			.tea-eval-comparison-diff.negative {
				background: #fee2e2;
				color: #991b1b;
			}

			.tea-eval-comparison-diff.zero {
				background: #f1f5f9;
				color: #475569;
			}

			.tea-eval-comparison-diff.missing {
				background: transparent;
				color: var(--text-muted);
				font-weight: 400;
			}
		`;
	},

	formatter(value, row, column, data, default_formatter) {
		const formatted_value = default_formatter(value, row, column, data);
		const fieldname = column.fieldname;

		if (fieldname && fieldname.startsWith("diff_")) {
			if (value === null || value === undefined || value === "") {
				return '<span class="tea-eval-comparison-cell"><span class="tea-eval-comparison-diff missing">—</span></span>';
			}

			const num = Number(value || 0);
			const sign = num > 0 ? "+" : "";
			const css_class = num > 0 ? "positive" : num < 0 ? "negative" : "zero";
			const display = sign + num;

			return (
				'<span class="tea-eval-comparison-cell"><span class="tea-eval-comparison-diff ' +
				css_class +
				'">' +
				display +
				"</span></span>"
			);
		}

		return `<span class="tea-eval-comparison-cell">${formatted_value}</span>`;
	},
};
