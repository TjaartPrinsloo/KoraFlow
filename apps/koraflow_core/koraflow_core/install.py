# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def after_install():
	"""Setup Sales Agent system after installation"""
	try:
		create_sales_agent_roles()
		# Note: We don't create a workspace anymore - we use a custom page at /app/sales-agent-dash
		# create_sales_agent_workspace()  # Removed - using custom page instead
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Error in Sales Agent setup: {str(e)}")
		# Don't fail installation if setup fails


def create_sales_agent_roles():
	"""Create Sales Agent and Sales Agent Manager roles"""
	
	# Sales Agent Role
	if not frappe.db.exists("Role", "Sales Agent"):
		role = frappe.get_doc({
			"doctype": "Role",
			"role_name": "Sales Agent",
			"desk_access": 1,
			"is_custom": 1
		})
		role.insert(ignore_permissions=True)
		frappe.msgprint(_("Created Sales Agent role"))
	
	# Sales Agent Manager Role
	if not frappe.db.exists("Role", "Sales Agent Manager"):
		role = frappe.get_doc({
			"doctype": "Role",
			"role_name": "Sales Agent Manager",
			"desk_access": 1,
			"is_custom": 1
		})
		role.insert(ignore_permissions=True)
		frappe.msgprint(_("Created Sales Agent Manager role"))


# Workspace creation removed - Sales Agents now use custom Page (/app/sales-agent-dash) instead
# def create_sales_agent_workspace():
# 	"""Create Sales Agent Dashboard Workspace"""
# 	# No longer needed - using custom Page instead
# 	pass

