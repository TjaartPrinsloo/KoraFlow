import frappe

def get_context(context):
	context.no_cache = 1
	user = frappe.session.user
	if user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect
	
	sales_agent = frappe.db.get_value("Sales Agent", {"user": user}, ["name", "bank_details"], as_dict=True)
	
	context.bank = {
		"bank_name": "",
		"account_holder": "",
		"account_number": "",
		"branch_code": "",
		"account_type": ""
	}
	
	if sales_agent and sales_agent.bank_details:
		lines = sales_agent.bank_details.split('\n')
		if len(lines) >= 5:
			context.bank = {
				"bank_name": lines[0],
				"account_holder": lines[1],
				"account_number": lines[2],
				"branch_code": lines[3],
				"account_type": lines[4]
			}
