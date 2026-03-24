
import frappe
import json

def get_context(context):
	context.no_cache = 1

	user = frappe.session.user
	if user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	from koraflow_core.api.sales_agent_dashboard import (
		get_dashboard_data,
		get_crm_data,
		get_followups_due,
	)

	try:
		context.dashboard_data = json.dumps(get_dashboard_data() or {})
	except Exception:
		context.dashboard_data = "{}"

	try:
		context.crm_data = json.dumps(get_crm_data() or {})
	except Exception:
		context.crm_data = "{}"

	try:
		context.followups_data = json.dumps(get_followups_due() or {})
	except Exception:
		context.followups_data = "{}"
