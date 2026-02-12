# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def on_login(login_manager):
	"""
	Hook called after user login (before set_user_info).
	Sets default_route for client-side routing.
	Note: home_page set here gets overwritten by set_user_info(),
	so we use on_session_creation for the actual home_page override.
	"""
	user = login_manager.user
	roles = frappe.get_roles(user)

	# Set default_route (this survives set_user_info)
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		frappe.local.response["default_route"] = "/sales_agent_dashboard"

		# Clear default workspace so set_user_info doesn't redirect to /app/<workspace>
		try:
			user_doc = frappe.get_doc("User", user)
			if user_doc.default_workspace:
				user_doc.default_workspace = None
				user_doc.save(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error clearing default workspace for {user}: {str(e)}")

	elif "Patient" in roles:
		frappe.local.response["default_route"] = "/dashboard"


def on_session_creation(login_manager=None):
	"""
	Hook called AFTER set_user_info() — the right place to override home_page.
	Unlike on_login, values set here are NOT overwritten by Frappe's auth flow.
	Actually, set_user_info() runs just after make_session() which triggers this,
	so we set both home_page and default_route here.
	"""
	if frappe.session.user == "Guest":
		return

	roles = frappe.get_roles()

	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		frappe.local.response["home_page"] = "/sales_agent_dashboard"
		frappe.local.response["default_route"] = "/sales_agent_dashboard"
	elif "Patient" in roles:
		frappe.local.response["home_page"] = "/dashboard"
		frappe.local.response["default_route"] = "/dashboard"


def get_website_user_home_page(user):
	"""
	Hook for get_website_user_home_page — called by get_home_page()
	to determine the home page for Website Users.
	Returns the dashboard path for Patients.
	"""
	roles = frappe.get_roles(user)
	if "Patient" in roles:
		return "/dashboard"
	return None


def redirect_sales_agents():
	"""
	Before request hook to redirect Sales Agents from /app routes to dashboard
	"""
	if frappe.session.user == "Guest":
		return

	roles = frappe.get_roles()
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		path = frappe.local.request.path if hasattr(frappe.local, "request") and frappe.local.request else ""

		if path in ["/app/build", "/app/home", "/app/sales-agent-dashboard", "/app/user-profile"]:
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/sales_agent_dashboard"
			return
