"""
Sales Partner Query Controller
"""
import frappe
from frappe.model.document import Document


class SalesPartnerQuery(Document):
	def validate(self):
		"""Validate query data"""
		from frappe.utils import now
		if not self.created_on:
			self.created_on = now()
	
	def has_permission(self, ptype, user):
		"""Check if user has permission to access this query"""
		# System Managers can access all
		if "System Manager" in frappe.get_roles(user):
			return True
		
		# Sales Partners can only see their own queries
		if "Sales Partner Portal" in frappe.get_roles(user):
			# Get sales partner linked to user
			user_perms = frappe.get_all(
				"User Permission",
				filters={
					"user": user,
					"allow": "Sales Partner"
				},
				fields=["for_value"],
				limit=1
			)
			
			if user_perms and self.sales_partner == user_perms[0].for_value:
				return True
		
		return False


def get_permission_query_conditions(user):
	"""Filter queries by sales partner for portal users"""
	if "System Manager" in frappe.get_roles(user):
		return ""
	
	if "Sales Partner Portal" in frappe.get_roles(user):
		# Get sales partner linked to user
		user_perms = frappe.get_all(
			"User Permission",
			filters={
				"user": user,
				"allow": "Sales Partner"
			},
			fields=["for_value"],
			limit=1
		)
		
		if user_perms:
			sales_partner_name = user_perms[0].for_value
			return f"`tabSales Partner Query`.`sales_partner` = '{frappe.db.escape(sales_partner_name)}'"
	
	return ""

