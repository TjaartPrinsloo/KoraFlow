# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class CommissionRecord(Document):
	def validate(self):
		"""Validate commission record"""
		if not self.sales_agent and self.referral:
			# Fetch from referral
			referral = frappe.get_doc("Patient Referral", self.referral)
			self.sales_agent = referral.sales_agent
			self.sales_partner = referral.sales_partner
			self.referral_date = referral.referral_date
		
		# Mask invoice reference (show only last 4 chars)
		# This is handled in create_commission_from_invoice, but validate here too
		if self.invoice_reference and not self.invoice_reference.startswith("INV-****"):
			# Extract last 4 chars if it's a full invoice name
			if len(self.invoice_reference) > 4:
				self.invoice_reference = f"INV-****{self.invoice_reference[-4:]}"
	
	def before_insert(self):
		"""Set initial values"""
		if not self.commission_status:
			self.commission_status = "Pending"
		
		# Fetch referral data
		if self.referral:
			referral = frappe.get_doc("Patient Referral", self.referral)
			if not self.sales_agent:
				self.sales_agent = referral.sales_agent
			if not self.sales_partner:
				self.sales_partner = referral.sales_partner
			if not self.referral_date:
				self.referral_date = referral.referral_date


@frappe.whitelist()
def create_commission_from_invoice(sales_invoice, referral):
	"""Create commission record when invoice is paid"""
	if not sales_invoice or not referral:
		return None
	
	try:
		# Get invoice details
		invoice = frappe.get_doc("Sales Invoice", sales_invoice)
		referral_doc = frappe.get_doc("Patient Referral", referral)
		
		# Check if commission record already exists
		existing = frappe.db.get_value(
			"Commission Record",
			{"referral": referral, "invoice_reference": f"INV-****{sales_invoice[-4:]}"},
			"name"
		)
		
		if existing:
			return existing
		
		# Mask invoice reference (last 4 chars only)
		invoice_ref = sales_invoice
		if len(invoice_ref) > 4:
			invoice_ref = f"INV-****{invoice_ref[-4:]}"
		else:
			invoice_ref = f"INV-****{invoice_ref}"
		
		# Create commission record
		commission = frappe.get_doc({
			"doctype": "Commission Record",
			"referral": referral,
			"sales_agent": referral_doc.sales_agent,
			"sales_partner": referral_doc.sales_partner,
			"invoice_reference": invoice_ref,
			"commission_amount": invoice.total_commission or 0,
			"commission_status": "Pending",
			"referral_date": referral_doc.referral_date,
			"invoice_date": invoice.posting_date,
			"expected_payout_date": frappe.utils.add_days(invoice.posting_date, 30)  # 30 days default
		})
		
		commission.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return commission.name
		
	except Exception as e:
		frappe.log_error(title="Commission Record Error", message=f"Error creating commission record: {str(e)}")
		return None


@frappe.whitelist()
def get_agent_commissions(agent=None):
	"""Get all commission records for a sales agent"""
	if not agent:
		agent = frappe.session.user
	
	commissions = frappe.get_all(
		"Commission Record",
		filters={"sales_agent": agent},
		fields=[
			"name",
			"referral",
			"invoice_reference",
			"commission_amount",
			"commission_status",
			"referral_date",
			"invoice_date",
			"expected_payout_date",
			"paid_date"
		],
		order_by="referral_date desc"
	)
	
	return commissions

