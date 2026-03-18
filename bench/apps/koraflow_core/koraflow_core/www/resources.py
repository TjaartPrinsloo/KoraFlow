"""
Resources Page
"""
import frappe
from frappe import _

def get_context(context):
	# Resources page is disabled — redirect to dashboard
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/dashboard"
	raise frappe.Redirect
