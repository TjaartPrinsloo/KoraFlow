"""
Sales Partner API endpoints
"""
import frappe
from frappe import _


@frappe.whitelist()
def create_sales_partner_query(referral, subject, message):
	"""Create a Sales Partner Query"""
	# Check permissions
	user_roles = frappe.get_roles()
	if "Sales Partner Portal" not in user_roles:
		frappe.throw("Access Denied", frappe.PermissionError)
	
	# Get sales partner linked to user
	user_email = frappe.session.user
	user_permissions = frappe.get_all(
		"User Permission",
		filters={
			"user": user_email,
			"allow": "Sales Partner"
		},
		fields=["for_value"],
		limit=1
	)
	
	if not user_permissions:
		frappe.throw("No Sales Partner linked to your account", frappe.PermissionError)
	
	sales_partner_name = user_permissions[0].for_value
	
	# Verify referral belongs to this sales partner
	referral_doc = frappe.get_doc("Sales Partner Referral", referral)
	if referral_doc.sales_partner != sales_partner_name:
		frappe.throw("Access Denied", frappe.PermissionError)
	
	# Create query
	query = frappe.get_doc({
		"doctype": "Sales Partner Query",
		"sales_partner": sales_partner_name,
		"referral": referral,
		"subject": subject,
		"message": message,
		"status": "Open"
	})
	
	query.flags.ignore_permissions = True
	query.insert()
	frappe.db.commit()
	
	# Assign to Sales Team (you can customize this)
	# For now, assign to Administrator or create a Sales Team role
	sales_team_users = frappe.get_all(
		"User",
		filters={"enabled": 1},
		or_filters=[
			["roles", "role", "=", "Sales Manager"],
			["roles", "role", "=", "Sales User"]
		],
		fields=["name"],
		limit=1
	)
	
	if sales_team_users:
		query.assigned_to = sales_team_users[0].name
		query.save()
		frappe.db.commit()
	
	return {"name": query.name}


@frappe.whitelist()
def get_referral_summary():
	"""Get summary statistics for sales partner referrals"""
	# Check permissions
	user_roles = frappe.get_roles()
	if "Sales Partner Portal" not in user_roles:
		frappe.throw("Access Denied", frappe.PermissionError)
	
	# Get sales partner linked to user
	user_email = frappe.session.user
	user_permissions = frappe.get_all(
		"User Permission",
		filters={
			"user": user_email,
			"allow": "Sales Partner"
		},
		fields=["for_value"],
		limit=1
	)
	
	if not user_permissions:
		return {"error": "No Sales Partner linked"}
	
	sales_partner_name = user_permissions[0].for_value
	
	# Get referrals
	referrals = frappe.get_all(
		"Sales Partner Referral",
		filters={"sales_partner": sales_partner_name},
		fields=["referral_status"]
	)
	
	total = len(referrals)
	in_progress = len([r for r in referrals if r.referral_status not in ["Invoiced", "Paid"]])
	converted = len([r for r in referrals if r.referral_status in ["Order Confirmed", "Packing", "Dispatched", "Invoiced", "Paid"]])
	invoiced = len([r for r in referrals if r.referral_status in ["Invoiced", "Paid"]])
	
	return {
		"total_referrals": total,
		"in_progress": in_progress,
		"converted": converted,
		"invoiced": invoiced
	}

