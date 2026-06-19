// Copyright (c) 2026, BusinessThat.Works

frappe.query_reports["Holding Warehouse"] = {
	filters: [
		{
			fieldname: "acquisition_channel",
			label: "Acquisition Channel",
			fieldtype: "Select",
			options: "\nAuction\nPrivate\nOutsourced",
		},

		{
			fieldname: "lot_no",
			label: "Lot No",
			fieldtype: "Data",
		},

		{
			fieldname: "purchase_date",
			label: "Purchase Date",
			fieldtype: "Date",
		},

		{
			fieldname: "holding_status",
			label: "Holding Status",
			fieldtype: "Select",
			options: "\nCommitted\nReceived\nIn Stock",
		},

		{
			fieldname: "status",
			label: "Normal Status",
			fieldtype: "Select",
			options: "\nOffered\nEvaluated",
		},

		{
			fieldname: "mark",
			label: "Mark",
			fieldtype: "Link",
			options: "Mark",
		},

		{
			fieldname: "grade",
			label: "Grade",
			fieldtype: "Link",
			options: "Grade",
		},

		{
			fieldname: "seller",
			label: "Seller",
			fieldtype: "Link",
			options: "Seller",
		},

		{
			fieldname: "intended_segment",
			label: "Segment",
			fieldtype: "Link",
			options: "Tea Segment",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "holding_status") {
			if (data.holding_status == "Committed") {
				value = `
			<span style="
			background:#dcfce7;
			color:#166534;
			padding:4px 10px;
			border-radius:10px;
			font-weight:600;">
			${value}
			</span>
			`;
			}

			if (data.holding_status == "Received") {
				value = `
			<span style="
			background:#dbeafe;
			color:#1e40af;
			padding:4px 10px;
			border-radius:10px;
			font-weight:600;">
			${value}
			</span>
			`;
			}
		}

		return value;
	},
};
