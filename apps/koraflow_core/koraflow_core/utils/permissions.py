# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def get_patient_referral_permission_query_conditions(user):
	"""
	Build permission query conditions for Patient Referral
	Sales Agents can only see their own referrals
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager can see all
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return ""
	
	# Sales Agents can only see their own referrals
	if "Sales Agent" in frappe.get_roles(user):
		return f"`tabPatient Referral`.`sales_agent` = '{user}'"
	
	# Default: no access
	return "1=0"


def has_patient_referral_permission(doc, user=None, raise_exception=False):
	"""
	Check if user has permission for Patient Referral document
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager have full access
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return True
	
	# Sales Agents can only access their own referrals
	if "Sales Agent" in frappe.get_roles(user):
		if doc.sales_agent == user:
			return True
		else:
			if raise_exception:
				frappe.throw(_("You don't have permission to access this referral"))
			return False
	
	# Default: no access
	if raise_exception:
		frappe.throw(_("You don't have permission to access this document"))
	return False


def get_referral_message_permission_query_conditions(user):
	"""
	Build permission query conditions for Referral Message
	Users can only see messages they sent or received
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager can see all
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return ""
	
	# Users can see messages they sent or received
	return f"(`tabReferral Message`.`from_user` = '{user}' OR `tabReferral Message`.`to_user` = '{user}')"


def has_referral_message_permission(doc, user=None, raise_exception=False):
	"""
	Check if user has permission for Referral Message document
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager have full access
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return True
	
	# Users can only access messages they sent or received
	if doc.from_user == user or doc.to_user == user:
		return True
	
	if raise_exception:
		frappe.throw(_("You don't have permission to access this message"))
	return False


def restrict_patient_access():
	"""
	Ensure Sales Agents cannot access Patient records directly
	This should be called via hooks
	"""
	user_roles = frappe.get_roles()
	
	if "Sales Agent" in user_roles and "System Manager" not in user_roles:
		# Block access to Patient DocType
		frappe.throw(
			_("Sales Agents do not have permission to access Patient records directly. Please use Patient Referral instead."),
			frappe.PermissionError
		)


def get_commission_record_permission_query_conditions(user):
	"""
	Build permission query conditions for Commission Record
	Sales Agents can only see their own commission records
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager can see all
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return ""
	
	# Sales Agents can only see their own commission records
	if "Sales Agent" in frappe.get_roles(user):
		return f"`tabCommission Record`.`sales_agent` = '{user}'"
	
	# Default: no access
	return "1=0"


def has_commission_record_permission(doc, user=None, raise_exception=False):
	"""
	Check if user has permission for Commission Record document
	"""
	if not user:
		user = frappe.session.user
	
	# System Manager and Sales Agent Manager have full access
	if "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user):
		return True
	
	# Sales Agents can only access their own commission records
	if "Sales Agent" in frappe.get_roles(user):
		if doc.sales_agent == user:
			return True
		else:
			if raise_exception:
				frappe.throw(_("You don't have permission to access this commission record"))
			return False
	
	# Default: no access
	if raise_exception:
		frappe.throw(_("You don't have permission to access this document"))
	return False

