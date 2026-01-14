# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Permissions
Role-based permissions for GLP-1 dispensing system
"""

import frappe
from frappe import _


def get_glp1_prescription_permission_query_conditions(user):
	"""Permission query for GLP-1 Patient Prescription"""
	user_roles = frappe.get_roles(user)
	
	# Doctors can only see their own prescriptions
	if "Healthcare Practitioner" in user_roles:
		return f"""(`tabGLP-1 Patient Prescription`.doctor = '{user}')"""
	
	# Pharmacists and Compliance Officers can see all
	if "Pharmacist" in user_roles or "Compliance Officer" in user_roles:
		return ""
	
	# Sales/Promoters cannot see prescriptions
	if "Sales Agent" in user_roles or "Sales Partner" in user_roles:
		return "1=0"  # No access
	
	return ""


def has_glp1_prescription_permission(doc, user, permission_type="read"):
	"""Check if user has permission for prescription"""
	user_roles = frappe.get_roles(user)
	
	# Sales/Promoters: NO ACCESS
	if "Sales Agent" in user_roles or "Sales Partner" in user_roles:
		return False
	
	# Doctors: can only see their own
	if "Healthcare Practitioner" in user_roles:
		return doc.doctor == user
	
	# Pharmacists, Compliance Officers, System Managers: full access
	if "Pharmacist" in user_roles or "Compliance Officer" in user_roles or "System Manager" in user_roles:
		return True
	
	return False


def get_glp1_stock_permission_query_conditions(user):
	"""Permission query for stock - Doctors cannot see quantities"""
	user_roles = frappe.get_roles(user)
	
	# Doctors: cannot see stock
	if "Healthcare Practitioner" in user_roles:
		return "1=0"  # No access to stock
	
	# Sales/Promoters: cannot see stock
	if "Sales Agent" in user_roles or "Sales Partner" in user_roles:
		return "1=0"
	
	return ""


def has_glp1_stock_permission(doc, user, permission_type="read"):
	"""Check if user can access stock"""
	user_roles = frappe.get_roles(user)
	
	# Doctors and Sales: NO ACCESS
	if "Healthcare Practitioner" in user_roles or "Sales Agent" in user_roles or "Sales Partner" in user_roles:
		return False
	
	# Pharmacists, Compliance Officers, System Managers: full access
	if "Pharmacist" in user_roles or "Compliance Officer" in user_roles or "System Manager" in user_roles:
		return True
	
	return False


def get_glp1_dispense_task_permission_query_conditions(user):
	"""Permission query for dispense tasks"""
	user_roles = frappe.get_roles(user)
	
	# Only Pharmacists can see dispense tasks
	if "Pharmacist" not in user_roles and "System Manager" not in user_roles:
		return "1=0"
	
	return ""


def has_glp1_dispense_task_permission(doc, user, permission_type="read"):
	"""Check if user can access dispense tasks"""
	user_roles = frappe.get_roles(user)
	
	# Only Pharmacists
	if "Pharmacist" in user_roles or "System Manager" in user_roles:
		return True
	
	return False
