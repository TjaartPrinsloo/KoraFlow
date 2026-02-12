# Copyright (c) 2026, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""Context for compliance page"""
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.throw("Please login to access this page", frappe.PermissionError)
	
	# Add page title and metadata
	context.title = "Regulatory Compliance"
	context.no_cache = 1
	
	return context
