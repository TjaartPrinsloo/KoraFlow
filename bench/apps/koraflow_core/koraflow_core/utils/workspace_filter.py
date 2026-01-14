# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


@frappe.whitelist()
def get_workspace_sidebar_items():
	"""
	Override get_workspace_sidebar_items to restrict Sales Agents
	Sales Agents should only see the Sales Agent Dashboard workspace
	"""
	from frappe.desk.desktop import get_workspace_sidebar_items as original_get_workspace_sidebar_items
	
	# Get original sidebar items
	sidebar_items = original_get_workspace_sidebar_items()
	
	roles = frappe.get_roles()
	
	# If user is a Sales Agent (and not a manager), restrict workspaces
	if "Sales Agent" in roles and "Sales Agent Manager" not in roles and "System Manager" not in roles:
		# Only show Welcome Workspace (custom page is accessed directly via /app/sales-agent-dash route)
		filtered_pages = []
		for page in sidebar_items.get("pages", []):
			# Only allow Welcome Workspace
			if page.get("name") == "Welcome Workspace":
				filtered_pages.append(page)
		
		sidebar_items["pages"] = filtered_pages
	
	return sidebar_items

