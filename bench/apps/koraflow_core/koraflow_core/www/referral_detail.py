"""
Portal page for viewing individual referral details
Route: /my-referrals/<referral_name>
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
	"""Get context for referral detail page"""
	# Check if user is a sales partner
	user_roles = frappe.get_roles()
	if "Sales Partner Portal" not in user_roles:
		frappe.throw("Access Denied", frappe.PermissionError)
	
	# Get referral name from route
	referral_name = frappe.form_dict.name
	
	if not referral_name:
		frappe.redirect_to_message(_("Referral Not Found"), _("Please select a referral from the list."))
		frappe.throw("")
	
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
	
	# Get referral (with permission check)
	try:
		# First verify referral exists and belongs to this sales partner
		referral_exists = frappe.db.exists(
			"Sales Partner Referral",
			{
				"name": referral_name,
				"sales_partner": sales_partner_name
			}
		)
		
		if not referral_exists:
			frappe.log_error(
				f"Permission violation: User {user_email} tried to access referral {referral_name}",
				"Sales Partner Permission Violation"
			)
			frappe.throw("Access Denied", frappe.PermissionError)
		
		referral = frappe.get_doc("Sales Partner Referral", referral_name)
		
		# Double-check this referral belongs to the sales partner
		if referral.sales_partner != sales_partner_name:
			frappe.log_error(
				f"Permission violation: User {user_email} tried to access referral {referral_name} belonging to {referral.sales_partner}",
				"Sales Partner Permission Violation"
			)
			frappe.throw("Access Denied", frappe.PermissionError)
		
		# Get commission data if invoiced
		# Note: Sales Partners can't read Sales Invoice directly
		# Commission data is accessed via reports instead
		commission_data = None
		if referral.sales_invoice:
			# Try to get commission via report query (filtered by sales_partner)
			# This is safer than direct access and respects permissions
			try:
				# Use report query to get commission data
				commission_query = """
					SELECT 
						sum(total_commission) as total_commission,
						avg(commission_rate) as commission_rate
					FROM `tabSales Invoice`
					WHERE name = %(invoice)s
					AND sales_partner = %(sales_partner)s
					AND docstatus = 1
				"""
				result = frappe.db.sql(
					commission_query,
					{
						"invoice": referral.sales_invoice,
						"sales_partner": sales_partner_name
					},
					as_dict=True
				)
				if result and result[0].get('total_commission'):
					commission_data = result[0]
			except Exception as e:
				# If query fails (likely due to permissions), commission_data remains None
				# User can still access commission via report link
				frappe.log_error(f"Could not fetch commission data: {str(e)}", "Sales Partner Commission")
				commission_data = None
		
		# Get queries/comments for this referral
		# Explicitly filter by sales_partner for data isolation
		queries = frappe.get_all(
			"Sales Partner Query",
			filters={
				"referral": referral_name,
				"sales_partner": sales_partner_name  # Extra security filter
			},
			fields=["name", "subject", "message", "status", "response", "created_on"],
			order_by="created_on desc",
			ignore_permissions=False  # Ensure permissions are checked
		)
		
		context.update({
			"referral": referral,
			"commission_data": commission_data,
			"queries": queries,
			"sales_partner": sales_partner_name,
			"get_status_badge_color": get_status_badge_color  # Add function to context
		})
		
	except frappe.DoesNotExistError:
		frappe.throw("Referral not found", frappe.DoesNotExistError)
	
	return context

