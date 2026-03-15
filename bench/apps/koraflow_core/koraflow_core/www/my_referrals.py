"""
Portal page for Sales Partners to view their referrals
Route: /my-referrals
"""
import frappe
from frappe import _
from frappe.utils import getdate, now_datetime


def get_status_badge_color(status):
	"""Get Bootstrap badge color class for referral status"""
	if status == "Paid":
		return "success"
	elif status == "Invoiced":
		return "info"
	elif status in ["Dispatched", "Order Confirmed"]:
		return "primary"
	elif status == "Packing":
		return "warning"
	elif status == "Quotation Sent":
		return "secondary"
	else:
		return "light"


def get_context(context):
	"""Get context for /my-referrals portal page"""
	# Check if user is a sales partner
	user_roles = frappe.get_roles()
	if "Sales Partner Portal" not in user_roles:
		frappe.throw("Access Denied", frappe.PermissionError)
	
	# Get sales partner linked to user
	user_email = frappe.session.user
	sales_partner = frappe.db.get_value(
		"User",
		user_email,
		"full_name"
	)
	
	# Find Sales Partner record linked to this user
	sales_partner_name = None
	user_permissions = frappe.get_all(
		"User Permission",
		filters={
			"user": user_email,
			"allow": "Sales Partner"
		},
		fields=["for_value"],
		limit=1
	)
	
	if user_permissions:
		sales_partner_name = user_permissions[0].for_value
	
	if not sales_partner_name:
		frappe.throw("No Sales Partner linked to your account", frappe.PermissionError)
	
	# Get referrals - explicitly filter by sales_partner for data isolation
	# This is redundant with permission_query_conditions but adds extra security
	referrals = frappe.get_all(
		"Sales Partner Referral",
		filters={"sales_partner": sales_partner_name},
		fields=[
			"name",
			"first_name",
			"last_name",
			"full_name",
			"referral_date",
			"referral_status",
			"last_updated"
		],
		order_by="referral_date desc",
		ignore_permissions=False  # Ensure permissions are checked
	)
	
	# Verify all referrals belong to this sales partner (extra security check)
	verified_referrals = []
	for referral in referrals:
		# Double-check permission
		try:
			referral_doc = frappe.get_doc("Sales Partner Referral", referral.name)
			if referral_doc.sales_partner == sales_partner_name:
				verified_referrals.append(referral)
			else:
				frappe.log_error(
					title="Sales Partner Permission Violation",
					message=f"Permission violation: User {user_email} tried to access referral {referral.name} belonging to {referral_doc.sales_partner}"
				)
		except frappe.PermissionError:
			# Permission denied - log and skip
			frappe.log_error(title="Referral Permission Error", message=f"User {user_email} (Partner: {sales_partner_name}) tried to access unauthorized referral {referral.name}")
			continue
		except Exception as e:
			# Other error - log and skip
			frappe.log_error(title="Referral Update Error", message=f"Partner check failed for referral {referral.name}: {str(e)}")
			continue
	
	referrals = verified_referrals
	
	# Calculate summary stats
	total_referrals = len(referrals)
	in_progress = len([r for r in referrals if r.referral_status not in ["Invoiced", "Paid"]])
	converted = len([r for r in referrals if r.referral_status in ["Order Confirmed", "Packing", "Dispatched", "Invoiced", "Paid"]])
	invoiced = len([r for r in referrals if r.referral_status in ["Invoiced", "Paid"]])
	
	# Get commission summary from report (Sales Partners can't read Sales Invoice directly)
	commission_summary = None
	try:
		# Use report query to get commission summary
		commission_query = """
			SELECT 
				sum(total_commission) as total_commission,
				count(*) as invoice_count
			FROM `tabSales Invoice`
			WHERE sales_partner = %(sales_partner)s
			AND docstatus = 1
			AND IFNULL(total_commission, 0) > 0
		"""
		result = frappe.db.sql(
			commission_query,
			{"sales_partner": sales_partner_name},
			as_dict=True
		)
		if result and result[0]:
			commission_summary = result[0]
	except Exception as e:
		# If query fails (likely due to permissions), commission_summary remains None
		# User can still access commission via report link
		frappe.log_error(title="Sales Partner Commission", message=f"Could not fetch commission summary: {str(e)}")
		commission_summary = None
	
	context.update({
		"sales_partner": sales_partner_name,
		"referrals": referrals,
		"summary": {
			"total_referrals": total_referrals,
			"in_progress": in_progress,
			"converted": converted,
			"invoiced": invoiced
		},
		"commission_summary": commission_summary,
		"get_status_badge_color": get_status_badge_color  # Add function to context
	})
	
	return context

