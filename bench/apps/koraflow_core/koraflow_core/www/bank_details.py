# Copyright (c) 2026, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""Context for bank details page"""
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.throw("Please login to access this page", frappe.PermissionError)
	
	# Check if user has Sales Agent role
	if not frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Sales Agent"}):
		frappe.throw("Only Sales Agents can access this page", frappe.PermissionError)
	
	# Add page title and metadata
	context.title = "Bank Details Management"
	context.no_cache = 1
	
	return context
