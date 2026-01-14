# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def resolve_sales_agent_route(route):
	"""
	Override route resolution for Sales Agents
	Redirect /app, /app/build, /app/home to /app/sales-agent-dash for Sales Agents
	
	This is called by Frappe's website router for client-side routes.
	"""
	if frappe.session.user == "Guest":
		return route
	
	# Check if user is a Sales Agent
	roles = frappe.get_roles()
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		# Normalize route (remove trailing slash)
		normalized_route = route.rstrip('/')
		
		# If route is /app, /app/build, /app/home, /app/user-profile, or /app/sales-agent-dashboard, redirect to /app/sales-agent-dash
		if normalized_route in ["/app", "/app/build", "/app/home", "/app/user-profile", "/app/sales-agent-dashboard"]:
			return "/app/sales-agent-dash"
	
	return route

