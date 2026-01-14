import frappe
from frappe import _


def get_context(context):
	"""Custom page handler for intake form"""
	context.no_cache = 1
	
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access this form"), frappe.PermissionError)
	
	# Check if patient already exists
	user_email = frappe.session.user
	patient_exists = frappe.db.get_value("Patient", {"email": user_email}, "name")
	
	context.patient_exists = bool(patient_exists)
	context.user_email = user_email
	
	# Get intake form status
	from koraflow_core.api.patient_signup import get_intake_form_status
	context.intake_status = get_intake_form_status(user_email)
	
	# If patient exists and intake is completed, redirect
	if context.patient_exists and context.intake_status.get("status") == "completed":
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/app/patient"

