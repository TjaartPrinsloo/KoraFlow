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
	context.intake_status = {"status": "pending"}
	context.patient = None
	
	# Check if user is logged in
	if frappe.session.user == "Guest":
		# For Guest users, just return basic context
		# The template will show login requirement
		return context
	
	# Check if user has Patient role
	if "Patient" not in frappe.get_roles():
		# Non-patient users get basic context
		return context
	
	# Get patient information
	try:
		user = frappe.get_doc("User", frappe.session.user)
		patient = None
		
		if frappe.db.exists("Patient", {"email": frappe.session.user}):
			patient = frappe.get_doc("Patient", {"email": frappe.session.user})
			if patient.glp1_intake_forms:
				# Check if any intake form is completed
				completed_forms = [
					f for f in patient.glp1_intake_forms 
					if f.intake_form and frappe.db.get_value("GLP-1 Intake Form", f.intake_form, "form_status") == "Completed"
				]
				if completed_forms:
					context.intake_status = {"status": "completed"}
					return context
		
		context.patient = patient
	except Exception as e:
		# If there's an error, just use default context
		frappe.log_error(title="Intake Wizard Context Error", message=f"Error in get_context for glp1_intake_wizard: {e}")
	
	return context
