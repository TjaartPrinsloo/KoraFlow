frappe.query_reports["Sales Agent Commission Summary"] = {
	filters: [
		{
			fieldname: "sales_agent",
			label: __("Sales Agent"),
			fieldtype: "Link",
			options: "Sales Agent",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nAll\nAccrued\nRequested\nPaid",
			default: "All",
		},
	],
};
