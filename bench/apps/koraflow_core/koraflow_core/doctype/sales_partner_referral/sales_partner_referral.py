"""
Sales Partner Referral Controller
"""
import frappe
from frappe.model.document import Document


class SalesPartnerReferral(Document):
	def validate(self):
		"""Validate referral data"""
		# Ensure patient is set (even though field is not reqd in form)
		if not self.patient:
			frappe.throw("Patient is required")
		
		# Auto-set full_name
		if self.first_name and self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}"
		
		# Update last_updated
		from frappe.utils import now
		self.last_updated = now()
	
	def before_insert(self):
		"""Set defaults before insert"""
		from frappe.utils import now
		if not self.referral_date:
			self.referral_date = frappe.utils.today()
		if not self.last_updated:
			self.last_updated = now()
	
	def on_update(self):
		"""Update last_updated on save"""
		from frappe.utils import now
		self.last_updated = now()
	
	def has_permission(self, ptype, user):
		"""Check if user has permission to access this referral"""
		# System Managers can access all
		if "System Manager" in frappe.get_roles(user):
			return True
		
		# Sales Partners can only see their own referrals
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
	"""Filter referrals by sales partner for portal users"""
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
			return f"`tabSales Partner Referral`.`sales_partner` = '{frappe.db.escape(sales_partner_name)}'"
	
	return ""


def update_referral_status_from_quotation(doc, method):
	"""Update referral status when Quotation is submitted"""
	if doc.doctype != "Quotation" or doc.docstatus != 1:
		return
	
	# Find referral linked to this quotation
	referrals = frappe.get_all(
		"Sales Partner Referral",
		filters={"quotation": doc.name},
		fields=["name"]
	)
	
	for ref in referrals:
		referral = frappe.get_doc("Sales Partner Referral", ref.name)
		if doc.docstatus == 1:  # Submitted
			referral.referral_status = "Quotation Sent"
			referral.quotation = doc.name
			referral.flags.ignore_permissions = True
			referral.save()


def update_referral_status_from_sales_order(doc, method):
	"""Update referral status when Sales Order is submitted"""
	if doc.doctype != "Sales Order" or doc.docstatus != 1:
		return
	
	# Find referral linked to this sales order (via quotation or direct)
	referrals = frappe.get_all(
		"Sales Partner Referral",
		filters={"sales_order": doc.name},
		fields=["name"]
	)
	
	# Also check via quotation
	if doc.quotation:
		quotation_refs = frappe.get_all(
			"Sales Partner Referral",
			filters={"quotation": doc.quotation},
			fields=["name"]
		)
		referrals.extend(quotation_refs)
	
	for ref in referrals:
		referral = frappe.get_doc("Sales Partner Referral", ref.name)
		if doc.docstatus == 1:  # Submitted
			referral.referral_status = "Order Confirmed"
			referral.sales_order = doc.name
			referral.flags.ignore_permissions = True
			referral.save()


def update_referral_status_from_delivery_note(doc, method):
	"""Update referral status when Delivery Note is submitted"""
	if doc.doctype != "Delivery Note":
		return
	
	# Find referral via sales order
	if doc.items:
		sales_orders = list(set([item.against_sales_order for item in doc.items if item.against_sales_order]))
		for so in sales_orders:
			referrals = frappe.get_all(
				"Sales Partner Referral",
				filters={"sales_order": so},
				fields=["name"]
			)
			
			for ref in referrals:
				referral = frappe.get_doc("Sales Partner Referral", ref.name)
				if doc.docstatus == 0:  # Draft
					referral.referral_status = "Packing"
				elif doc.docstatus == 1:  # Submitted
					referral.referral_status = "Dispatched"
				referral.delivery_note = doc.name
				referral.flags.ignore_permissions = True
				referral.save()


def update_referral_status_from_sales_invoice(doc, method):
	"""Update referral status when Sales Invoice is submitted"""
	if doc.doctype != "Sales Invoice" or doc.docstatus != 1:
		return
	
	# Find referral via sales order or direct link
	referrals = frappe.get_all(
		"Sales Partner Referral",
		filters={"sales_invoice": doc.name},
		fields=["name"]
	)
	
	# Also check via sales order
	if doc.items:
		sales_orders = list(set([item.sales_order for item in doc.items if item.sales_order]))
		for so in sales_orders:
			so_refs = frappe.get_all(
				"Sales Partner Referral",
				filters={"sales_order": so},
				fields=["name"]
			)
			referrals.extend(so_refs)
	
	for ref in referrals:
		referral = frappe.get_doc("Sales Partner Referral", ref.name)
		if doc.docstatus == 1:  # Submitted
			referral.referral_status = "Invoiced"
			referral.sales_invoice = doc.name
			referral.flags.ignore_permissions = True
			referral.save()


def update_referral_status_from_payment_entry(doc, method):
	"""Update referral status when Payment Entry is submitted"""
	if doc.doctype != "Payment Entry" or doc.docstatus != 1:
		return
	
	# Find referral via sales invoice
	if doc.references:
		for ref in doc.references:
			if ref.reference_doctype == "Sales Invoice":
				referrals = frappe.get_all(
					"Sales Partner Referral",
					filters={"sales_invoice": ref.reference_name},
					fields=["name"]
				)
				
				for ref_doc in referrals:
					referral = frappe.get_doc("Sales Partner Referral", ref_doc.name)
					if doc.docstatus == 1:  # Submitted
						referral.referral_status = "Paid"
						referral.payment_entry = doc.name
						referral.flags.ignore_permissions = True
						referral.save()
