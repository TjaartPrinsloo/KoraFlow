import frappe
from frappe.utils import flt

def get_context(context):
	context.no_cache = 1
	user = frappe.session.user
	if user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect
	
	sales_agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not sales_agent:
		context.available_balance = 0.0
		return

	# Calculate available balance (Same logic as dashboard/API)
	accruals = frappe.get_all("Sales Agent Accrual", 
		filters={"sales_agent": sales_agent, "status": "Accrued"},
		fields=["accrued_amount"]
	)
	context.available_balance = sum(flt(d.accrued_amount) for d in accruals)
