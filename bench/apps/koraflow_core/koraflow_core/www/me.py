# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	"""Custom context for My Account page with Sales Agent features"""
	if frappe.session.user == "Guest":
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.current_user = frappe.get_doc("User", frappe.session.user)
	context.show_sidebar = True
	
	# Check if user has Sales Agent role
	context.is_sales_agent = frappe.db.exists(
		"Has Role",
		{"parent": frappe.session.user, "role": "Sales Agent"}
	)
