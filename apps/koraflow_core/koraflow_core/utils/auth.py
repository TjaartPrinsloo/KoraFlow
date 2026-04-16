# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from werkzeug.exceptions import abort as _abort
from werkzeug.utils import redirect as _redirect


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
			frappe.log_error(title="Workspace Reset Error", message=f"Error clearing default workspace for {user}: {str(e)}")

	elif "Pharmacist" in roles and "System Manager" not in roles:
		frappe.local.response["default_route"] = "/app/pharmacy"

	elif ("Nurse" in roles or "Clinical Viewer" in roles) and "System Manager" not in roles:
		frappe.local.response["default_route"] = "/app/medical-dashboard"

	elif "Patient" in roles:
		frappe.local.response["default_route"] = "/dashboard"

	else:
		frappe.local.response["default_route"] = "/app/"


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
	elif "Pharmacist" in roles and "System Manager" not in roles:
		frappe.local.response["home_page"] = "/app/pharmacy"
		frappe.local.response["default_route"] = "/app/pharmacy"
	elif ("Nurse" in roles or "Clinical Viewer" in roles) and "System Manager" not in roles:
		frappe.local.response["home_page"] = "/app/medical-dashboard"
		frappe.local.response["default_route"] = "/app/medical-dashboard"
	elif "Patient" in roles:
		frappe.local.response["home_page"] = "/dashboard"
		frappe.local.response["default_route"] = "/dashboard"
	else:
		frappe.local.response["home_page"] = "/app/"
		frappe.local.response["default_route"] = "/app/"


def get_website_user_home_page(user):
	"""
	Hook for get_website_user_home_page — called by get_home_page()
	to determine the home page for Website Users.
	"""
	roles = frappe.get_roles(user)
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		return "sales_agent_dashboard"
	if "Patient" in roles:
		return "dashboard"
	return None


def redirect_sales_agents():
	"""
	Before request hook to redirect Sales Agents from /app routes to dashboard.
	Sales Agents should ONLY see the partner portal pages.
	"""
	if frappe.session.user == "Guest":
		return

	roles = frappe.get_roles()
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		path = frappe.local.request.path if hasattr(frappe.local, "request") and frappe.local.request else ""

		# Allow these paths for sales agents
		allowed_prefixes = (
			"/sales_agent_dashboard",
			"/sales_agent_portal",
			"/sales_agent_profile",
			"/sales_agent_help",
			"/sales-agent-portal",
			"/api/",
			"/assets/",
			"/s2w_login",
			"/login",
			"/logout",
		)

		if path and not path.startswith(allowed_prefixes):
			_abort(_redirect("/sales_agent_dashboard"))

		# Also override home_page on every request so Frappe SPA doesn't route elsewhere
		frappe.local.response["home_page"] = "/sales_agent_dashboard"


def redirect_patients():
	"""
	Before request hook to redirect Patients from /app routes to the patient dashboard.
	Patients should only see the patient portal, not the Frappe desk.
	"""
	if frappe.session.user == "Guest":
		return

	roles = frappe.get_roles()
	if "Patient" in roles and "System Manager" not in roles and "Healthcare Administrator" not in roles:
		path = frappe.local.request.path if hasattr(frappe.local, "request") and frappe.local.request else ""

		# Allow these paths for patients
		allowed_prefixes = (
			"/dashboard",
			"/me",
			"/glp1",
			"/intake",
			"/patient",
			"/api/",
			"/assets/",
			"/s2w_login",
			"/login",
			"/logout",
		)

		if path and path.startswith("/app/") and not path.startswith(allowed_prefixes):
			_abort(_redirect("/dashboard"))

		# Override home_page on every request
		frappe.local.response["home_page"] = "/dashboard"


def on_logout(login_manager):
	"""
	Hook called after user logout.
	Redirects to branded login page.
	"""
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/s2w_login"


@frappe.whitelist(allow_guest=True)
def logout():
	frappe.local.login_manager.logout()
	frappe.db.commit()
	frappe.respond_as_web_page(
		"Logging out...",
		"""<script>window.location.href = '/s2w_login';</script>""",
		http_status_code=200,
	)
