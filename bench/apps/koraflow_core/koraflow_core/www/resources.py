"""
Resources Page
"""
import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access this page"), frappe.PermissionError)
	
	if "Patient" not in frappe.get_roles():
		frappe.throw(_("Access denied"), frappe.PermissionError)
	
	patient = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	
	if not patient:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/glp1-intake"
		return
	
	context.patient = frappe.get_doc("Patient", patient)
