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
		frappe.log_error(title="Sales Agent Setup Error", message=f"Error in Sales Agent setup: {str(e)}")
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


def apply_property_setters():
	"""Apply property setters for core DocType field overrides.
	Runs after every migrate to ensure options stay in sync."""
	setters = {
		("Patient", "status", "options"): "Active\nDisabled\nUnder Review",
	}

	for (dt, field, prop), value in setters.items():
		existing = frappe.db.get_value("Property Setter", {
			"doc_type": dt,
			"field_name": field,
			"property": prop
		})
		if existing:
			frappe.db.set_value("Property Setter", existing, "value", value)
		else:
			frappe.get_doc({
				"doctype": "Property Setter",
				"doctype_or_field": "DocField",
				"doc_type": dt,
				"field_name": field,
				"property": prop,
				"value": value,
				"property_type": "Small Text",
			}).insert(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache(doctype="Patient")

