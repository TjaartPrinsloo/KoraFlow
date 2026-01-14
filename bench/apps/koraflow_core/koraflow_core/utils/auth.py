# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def on_login(login_manager):
	"""
	Hook called after user login
	Set default route and workspace for Sales Agents to /app/sales-agent-dash
	"""
	user = login_manager.user
	roles = frappe.get_roles(user)
	
	# If user is a Sales Agent (and not a manager), set default route
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		# Override home_page to redirect to custom dashboard page
		frappe.local.response["home_page"] = "/app/sales-agent-dash"
		
		# Also set it in the user's boot info for client-side routing
		if hasattr(frappe.local, "response"):
			frappe.local.response["default_route"] = "/app/sales-agent-dash"
		
		# Clear default workspace for Sales Agents
		# Since we're using a custom Page (/app/sales-agent-dash) instead of a workspace,
		# we should not set a default workspace. The home_page redirect will handle routing.
		try:
			user_doc = frappe.get_doc("User", user)
			if user_doc.default_workspace:
				user_doc.default_workspace = None
				user_doc.save(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			# If clearing workspace fails, continue anyway
			frappe.log_error(f"Error clearing default workspace for {user}: {str(e)}")


def redirect_sales_agents():
	"""
	Before request hook to redirect Sales Agents from /app/build, /app/home, /app/user-profile to dashboard
	Note: Client-side routes like /app/user-profile are handled by JavaScript, but we can inject redirect script
	"""
	if frappe.session.user == "Guest":
		return
	
	# Check if user is a Sales Agent
	roles = frappe.get_roles()
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		# Get the current path
		path = frappe.local.request.path if hasattr(frappe.local, "request") and frappe.local.request else ""
		
		# For server-side routes, do a proper redirect
		if path in ["/app/build", "/app/home", "/app/sales-agent-dashboard", "/app/user-profile"]:
			# Check if this is an AJAX request (client-side routing)
			is_ajax = frappe.local.is_ajax if hasattr(frappe.local, "is_ajax") else False
			
			if is_ajax:
				# For AJAX requests (client-side routing), return redirect response
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = "/app/sales-agent-dash"
			else:
				# For full page loads, do server-side redirect
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = "/app/sales-agent-dash"
			return

