# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Intake Form Wizard Page
Onboarding wizard for patient intake form
"""

import frappe
from frappe import _


def get_context(context):
	"""Get context for GLP-1 Intake Wizard page"""
	
	# Always set intake_status to prevent template errors
	# Set it on the context object directly (Frappe merges returned dict)
	context_dict = {
		"intake_status": {"status": "pending"},
		"patient": None
	}
	
	# Also set on context object for direct access
	context.intake_status = context_dict["intake_status"]
	context.patient = context_dict["patient"]
	
	# Check if user is logged in
	if frappe.session.user == "Guest":
		# For Guest users, just return basic context
		# The template will show login requirement
		return context_dict
	
	# Check if user has Patient role
	if "Patient" not in frappe.get_roles():
		# Non-patient users get basic context
		return context_dict
	
	# Get patient information
	try:
		patient = None
		if frappe.db.exists("Patient", {"email": frappe.session.user}):
			patient = frappe.get_doc("Patient", {"email": frappe.session.user})
			
			# Check if there is a completed intake submission using standalone DocType
			intake_forms = frappe.get_all("GLP-1 Intake Submission", filters={"patient": patient.name}, limit=1, ignore_permissions=True)
			if intake_forms:
				context_dict["intake_status"] = {"status": "completed"}
				context.intake_status = context_dict["intake_status"]
				return context_dict
		
		context_dict["patient"] = patient
		context.patient = patient
	except Exception as e:
		# If there's an error, just use default context
		frappe.log_error(title="Intake Wizard Context Error", message=f"Error in get_context for glp1_intake_wizard: {e}")
	
	# Return dict that will be merged into context
	return context_dict
