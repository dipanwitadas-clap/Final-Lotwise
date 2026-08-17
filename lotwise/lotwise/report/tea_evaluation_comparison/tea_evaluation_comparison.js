// Copyright (c) 2026, BusinessThat.Works

frappe.query_reports["Tea Evaluation Comparison"] = {
	filters: [
		{
			fieldname: "stage_1",
			label: __("Stage 1"),
			fieldtype: "Link",
			options: "Evaluation Stage",
			default: "Bag Sample",
		},
		{
			fieldname: "stage_2",
			label: __("Stage 2"),
			fieldtype: "Link",
			options: "Evaluation Stage",
			default: "Pre-purchase",
		},
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

			.tea-eval-comparison-report .report-summary {
				background: transparent;
				border-bottom: none;
				display: grid;
				grid-template-columns: 1fr;
				gap: 10px;
				margin: 0.75rem;
				padding: 0;
			}

			@media (min-width: 768px) {
				.tea-eval-comparison-report .report-summary {
					gap: 12px;
					grid-template-columns: repeat(2, 1fr);
					margin: 1rem;
				}
			}

			@media (min-width: 1200px) {
				.tea-eval-comparison-report .report-summary {
					grid-template-columns: repeat(4, 1fr);
				}
			}

			.tea-eval-comparison-report .report-summary .summary-item {
				background: var(--card-bg);
				border: 1px solid var(--border-color);
				border-radius: var(--border-radius-md, 8px);
				box-sizing: border-box;
				height: auto;
				margin: 0;
				overflow: hidden;
				padding: 14px 16px 12px;
				position: relative;
			}

			.tea-eval-comparison-report .report-summary .summary-item::before {
				background: var(--gray-400);
				content: "";
				height: 3px;
				left: 0;
				position: absolute;
				right: 0;
				top: 0;
			}

			.tea-eval-comparison-report .report-summary .summary-item:has(.summary-value.blue)::before {
				background: #0D1B2A;
			}

			.tea-eval-comparison-report .report-summary .summary-item:has(.summary-value.green)::before {
				background: #1B263B;
			}

			.tea-eval-comparison-report .report-summary .summary-item:has(.summary-value.orange)::before {
				background: #415A77;
			}

			.tea-eval-comparison-report .report-summary .summary-item:has(.summary-value.purple)::before {
				background: #778DA9;
			}

			.tea-eval-comparison-report .report-summary .summary-item:has(.summary-value.yellow)::before {
				background: #E0E1DD;
			}

			.tea-eval-comparison-report .report-summary .summary-label {
				color: var(--text-muted);
				font-size: 12px;
				font-weight: 600;
				letter-spacing: 0.02em;
				text-transform: uppercase;
			}

			.tea-eval-comparison-report .report-summary .summary-value,
			.tea-eval-comparison-report .report-summary .summary-value.blue,
			.tea-eval-comparison-report .report-summary .summary-value.green,
			.tea-eval-comparison-report .report-summary .summary-value.orange,
			.tea-eval-comparison-report .report-summary .summary-value.purple,
			.tea-eval-comparison-report .report-summary .summary-value.yellow {
				color: var(--text-color);
				font-size: 24px;
				font-weight: 700;
				line-height: 1.25;
				padding-bottom: 0;
				padding-top: 8px;
			}
		`;
	},

	get_datatable_options(options) {
		// Freeze the first 4 columns (Tea Lot, Lot No, Mark, Grade)
		options.columns = options.columns.map((col, index) => {
			if (index < 4) {
				col.sticky = true;
			}
			return col;
		});
		return options;
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
