import frappe
from koraflow_core.api.patient_signup import verify_email


def get_context(context):
	"""Handle email verification page"""
	token = frappe.form_dict.get("token")
	email = frappe.form_dict.get("email")
	
	if token:
		# Verify email
		verify_email(token, email)
		context.verified = True
	else:
		context.verified = False
		context.error = "Invalid verification link"

