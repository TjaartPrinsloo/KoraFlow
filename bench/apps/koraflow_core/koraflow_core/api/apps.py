import frappe
from frappe import _


@frappe.whitelist()
def get_apps():
	"""
	Override Frappe's get_apps to filter out blocked modules for users with Module Profile.
	This ensures Drive and other blocked modules don't appear in the apps dropdown.
	"""
	from frappe.desk.desktop import get_workspace_sidebar_items
	from frappe.apps import get_route as frappe_get_route
	from frappe.core.doctype.installed_applications.installed_applications import (
		get_apps_with_incomplete_dependencies,
		get_setup_wizard_completed_apps,
		get_setup_wizard_not_required_apps,
	)
	from frappe.desk.utils import slug

	allowed_workspaces = get_workspace_sidebar_items().get("pages")

	apps = frappe.get_installed_apps()
	app_list = []

	# Get user's blocked modules
	user = frappe.get_cached_doc("User", frappe.session.user)
	blocked_modules = user.get_blocked_modules() if hasattr(user, 'get_blocked_modules') else []

	for app in apps:
		if (
			app not in get_setup_wizard_completed_apps()
			and app not in get_setup_wizard_not_required_apps()
			and "System Manager" not in frappe.get_roles()
		):
			continue

		if app == "frappe":
			continue
		
		# Check if this app's module is blocked
		# Drive app corresponds to "Drive" module
		if app == "drive" and "Drive" in blocked_modules:
			continue
		
		app_details = frappe.get_hooks("add_to_apps_screen", app_name=app)
		if not len(app_details):
			continue
		for app_detail in app_details:
			try:
				has_permission_path = app_detail.get("has_permission")
				if has_permission_path:
					# Check permission first
					if not frappe.get_attr(has_permission_path)():
						continue
					# Also check if module is blocked (double check)
					if app == "drive" and "Drive" in blocked_modules:
						continue
				app_list.append(
					{
						"name": app,
						"logo": app_detail.get("logo"),
						"title": _(app_detail.get("title")),
						"route": get_route(app_detail, allowed_workspaces),
					}
				)
			except Exception:
				frappe.log_error(f"Failed to call has_permission hook ({has_permission_path}) for {app}")
	return app_list


def get_route(app, allowed_workspaces=None):
	"""Helper function to get route for app"""
	from frappe.desk.utils import slug
	
	if not allowed_workspaces:
		return "/app"

	route = app.get("route") if app and app.get("route") else "/apps"

	# Check if user has access to default workspace, if not, pick first workspace user has access to
	if route.startswith("/app/"):
		ws = route.split("/")[2]

		for allowed_ws in allowed_workspaces:
			if allowed_ws.get("name").lower() == ws.lower():
				return route

		module_app = frappe.local.module_app
		for allowed_ws in allowed_workspaces:
			module = allowed_ws.get("module")
			if module and module_app.get(module.lower()) == app.get("name"):
				return f"/app/{slug(allowed_ws.name.lower())}"
		return f"/app/{slug(allowed_workspaces[0].get('name').lower())}"
	else:
		return route

