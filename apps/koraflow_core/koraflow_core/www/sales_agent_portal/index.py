import frappe
from koraflow_core.koraflow_core.api.agent_portal import get_dashboard_data

def get_context(context):
	data = get_dashboard_data()
	if data.get("error"):
		context.no_access = True
	else:
		context.data = data
