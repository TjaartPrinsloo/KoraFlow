"""
Custom User DocType hooks for Patient signup
This file is kept for backward compatibility but the main logic
is now in koraflow_core.api.patient_signup.custom_sign_up
"""
import frappe
from frappe import _


def on_user_insert(doc, method):
	"""
	Hook into User after_insert to ensure Patient record exists
	This is a fallback in case the custom_sign_up method wasn't used
	
	Note: Notification Settings are created by Frappe's User.after_insert() method.
	If this hook is called, it means after_insert already ran, so we don't need to create
	Notification Settings again. However, if it failed, we'll try to create it here.
	"""
	# Only create Notification Settings if they don't exist (in case after_insert failed)
	# This is a safety net, but the main fix is in patient_sign_up() which overrides after_insert
	if not frappe.db.exists("Notification Settings", doc.name):
		try:
			from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings
			# Ensure we're running as Administrator
			original_user = frappe.session.user
			try:
				frappe.set_user("Administrator")
				frappe.flags.ignore_permissions = True
				create_notification_settings(doc.name)
			finally:
				frappe.flags.ignore_permissions = False
				frappe.set_user(original_user)
		except Exception as e:
			# Log but don't fail - notification settings are not critical
			frappe.log_error(f"Error creating notification settings for {doc.name}: {str(e)}", "User Creation")
	
	# Skip if flag is set (custom_sign_up will handle it)
	if hasattr(doc.flags, 'skip_patient_creation_hook') and doc.flags.skip_patient_creation_hook:
		return
	
	# Only process if user_type is "Patient" and no Patient record exists
	if doc.user_type == "Patient":
		if not frappe.db.get_value("Patient", {"email": doc.email}, "name"):
			try:
				from koraflow_core.api.patient_signup import create_patient_for_user
				create_patient_for_user(doc)
			except Exception as e:
				# Log error but don't raise - don't prevent user creation
				frappe.log_error(f"Error in on_user_insert for {doc.email}: {str(e)}")
				# Don't raise the exception - allow user creation to complete

