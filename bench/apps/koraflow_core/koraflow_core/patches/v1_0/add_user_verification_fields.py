"""
Add email verification and intake completion fields to User DocType
"""
import frappe


def execute():
	"""Add custom fields to User DocType for email verification and intake tracking"""
	fields_to_add = [
		{
			"fieldname": "email_verified",
			"fieldtype": "Check",
			"label": "Email Verified",
			"default": 0,
			"insert_after": "email",
			"read_only": 1,
			"description": "Whether the user's email has been verified"
		},
		{
			"fieldname": "email_verified_on",
			"fieldtype": "Datetime",
			"label": "Email Verified On",
			"insert_after": "email_verified",
			"read_only": 1,
			"description": "Timestamp when email was verified"
		},
		{
			"fieldname": "email_verified_via",
			"fieldtype": "Select",
			"label": "Email Verified Via",
			"options": "Email\nAdmin",
			"insert_after": "email_verified_on",
			"read_only": 1,
			"description": "Method used to verify email"
		},
		{
			"fieldname": "email_verified_by",
			"fieldtype": "Link",
			"options": "User",
			"label": "Email Verified By",
			"insert_after": "email_verified_via",
			"read_only": 1,
			"description": "User who verified email (if admin verified)"
		},
		{
			"fieldname": "email_verification_key",
			"fieldtype": "Data",
			"label": "Email Verification Key",
			"hidden": 1,
			"insert_after": "email_verified_by",
			"description": "Hashed verification token"
		},
		{
			"fieldname": "email_verification_key_generated_on",
			"fieldtype": "Datetime",
			"label": "Email Verification Key Generated On",
			"hidden": 1,
			"insert_after": "email_verification_key",
			"description": "When verification token was generated"
		},
		{
			"fieldname": "email_verification_reason",
			"fieldtype": "Small Text",
			"label": "Email Verification Reason",
			"insert_after": "email_verification_key_generated_on",
			"read_only": 1,
			"description": "Reason for admin verification (if applicable)"
		},
		{
			"fieldname": "intake_completed",
			"fieldtype": "Check",
			"label": "Intake Completed",
			"default": 0,
			"insert_after": "email_verification_reason",
			"read_only": 1,
			"description": "Whether the patient has completed the intake form"
		}
	]
	
	for field_def in fields_to_add:
		fieldname = field_def["fieldname"]
		if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
			custom_field = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "User",
				**field_def
			})
			custom_field.insert(ignore_permissions=True)
			frappe.logger().info(f"Added custom field: {fieldname} to User DocType")
		else:
			frappe.logger().info(f"Custom field {fieldname} already exists for User DocType")
	
	frappe.db.commit()
	frappe.clear_cache(doctype="User")

