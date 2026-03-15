import frappe
from frappe.apps import get_apps as original_get_apps

@frappe.whitelist(allow_guest=True)
def get_apps():
	apps = original_get_apps()
	KNOWN_APPS = ["erpnext", "crm", "drive", "gameplan", "insights", "hrms"]
	for app in apps:
		app_name = app.get("name")
		if app_name in KNOWN_APPS:
			app["logo"] = f"/assets/koraflow_core/images/apps/{app_name}.png"
		else:
			app["logo"] = "/assets/koraflow_core/images/koraflow_icon.png"
			
		title = app.get("title", "")
		# Clean Frappe prefix
		if title.startswith("Frappe "):
			title = title[7:]
		
		# Clean KoraFlow prefix
		if title.startswith("KoraFlow "):
			title = title[9:]
			
		app["title"] = title.strip()
			
	return apps

# Monkey patch the underlying function for internal python calls (like /apps page)
frappe.apps.get_apps = get_apps
