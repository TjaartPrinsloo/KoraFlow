# Copyright (c) 2025, KoraFlow and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute():
	"""Add unique constraints to mobile field in Patient DocType"""
	
	# Get Patient DocType
	patient_doctype = frappe.get_doc("DocType", "Patient")
	
	# Find mobile field
	mobile_field = None
	for field in patient_doctype.fields:
		if field.fieldname == "mobile":
			mobile_field = field
			break
	
	if mobile_field:
		# Check if there are any duplicate mobile numbers
		duplicates = frappe.db.sql("""
			SELECT mobile, COUNT(*) as count
			FROM `tabPatient`
			WHERE mobile IS NOT NULL AND mobile != ''
			GROUP BY mobile
			HAVING count > 1
			LIMIT 1
		""", as_dict=True)
		
		if duplicates:
			frappe.log_error(
				f"Cannot set mobile as unique: Found duplicate mobile numbers in Patient table. "
				f"Please resolve duplicates before running this patch.",
				"Unique Constraint Patch Error"
			)
			frappe.msgprint(
				_("Cannot set mobile as unique: Found duplicate mobile numbers. Please resolve duplicates first."),
				title=_("Patch Warning")
			)
		else:
			# Set mobile field as unique
			mobile_field.unique = 1
			patient_doctype.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(_("Added unique constraint to mobile field in Patient DocType"))
	else:
		frappe.log_error("Mobile field not found in Patient DocType", "Unique Constraint Patch Error")

