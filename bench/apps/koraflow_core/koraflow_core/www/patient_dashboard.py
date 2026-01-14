"""
Patient Dashboard Page
Custom dashboard view for Patient users
"""
import frappe
from frappe import _


def get_context(context):
	"""Get context for patient dashboard"""
	context.no_cache = 1
	
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access your dashboard"), frappe.PermissionError)
	
	# Check if user has Patient role
	if "Patient" not in frappe.get_roles():
		frappe.throw(_("Access denied. This page is only for patients."), frappe.PermissionError)
	
	# Get patient record
	patient = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	
	if not patient:
		# Redirect to intake form if patient doesn't exist
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/glp1-intake"
		return
	
	patient_doc = frappe.get_doc("Patient", patient)
	context.patient = patient_doc
	
	# Check intake form status
	from koraflow_core.api.patient_signup import get_intake_form_status
	intake_status = get_intake_form_status()
	context.intake_status = intake_status
	
	# Get intake forms
	intake_forms = frappe.get_all(
		"GLP-1 Intake Form",
		filters={"parent": patient},
		fields=["name", "form_status", "completion_date", "creation"],
		order_by="creation desc",
		limit=5
	)
	context.intake_forms = intake_forms
	
	# Page title
	context.title = _("Patient Dashboard")

