# Copyright (c) 2026, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, format_datetime


class PayoutRequest(Document):
	def validate(self):
		"""Validate payout request before saving"""
		# Set request date if not set
		if not self.request_date:
			self.request_date = now_datetime()
		
		# Validate sales agent role
		if not frappe.db.exists("Has Role", {"parent": self.sales_agent, "role": "Sales Agent"}):
			frappe.throw("User must have Sales Agent role to request payout")
		
		# Validate amount
		if self.amount <= 0:
			frappe.throw("Payout amount must be greater than zero")
		
		# Check available balance
		available_balance = get_available_balance(self.sales_agent)
		if self.amount > available_balance:
			frappe.throw(f"Requested amount ({self.amount}) exceeds available balance ({available_balance})")
		
		# Store bank details as text for reference
		if self.payment_method:
			bank_doc = frappe.get_doc("Sales Agent Bank Details", self.payment_method)
			self.bank_details = f"{bank_doc.bank_name} ({bank_doc.account_type}) - **** {bank_doc.masked_account_number[-4:]}"
	
	def on_update(self):
		"""Handle status changes"""
		# Set approval date when approved
		if self.status == "Approved" and not self.approval_date:
			self.approval_date = now_datetime()
			if not self.approved_by:
				self.approved_by = frappe.session.user
		
		# Set processed date when paid
		if self.status == "Paid" and not self.processed_date:
			self.processed_date = now_datetime()
	
	def before_submit(self):
		"""Actions before submit"""
		pass
	
	def on_submit(self):
		"""Actions on submit"""
		# Send notification email
		send_payout_notification(self)


def get_available_balance(sales_agent):
	"""Get available payout balance for sales agent"""
	from koraflow_core.api.sales_agent_dashboard import get_dashboard_data
	
	# Get commission summary
	summary = frappe.db.sql("""
		SELECT 
			SUM(CASE WHEN commission_status = 'Pending' THEN commission_amount ELSE 0 END) as pending
		FROM `tabCommission Record`
		WHERE sales_agent = %(sales_agent)s
	""", {"sales_agent": sales_agent}, as_dict=True)
	
	pending = summary[0].pending if summary and summary[0].pending else 0
	
	# Subtract pending payout requests
	pending_requests = frappe.db.sql("""
		SELECT SUM(amount) as total
		FROM `tabPayout Request`
		WHERE sales_agent = %(sales_agent)s
		AND status IN ('Submitted', 'Under Review', 'Approved')
	""", {"sales_agent": sales_agent}, as_dict=True)
	
	pending_payouts = pending_requests[0].total if pending_requests and pending_requests[0].total else 0
	
	return pending - pending_payouts


def send_payout_notification(doc):
	"""Send email notification for payout request"""
	try:
		# Get sales agent email
		user_email = frappe.db.get_value("User", doc.sales_agent, "email")
		
		# Send email
		frappe.sendmail(
			recipients=[user_email],
			subject=f"Payout Request {doc.name} Submitted",
			message=f"""
				<p>Your payout request has been submitted successfully.</p>
				<p><strong>Request ID:</strong> {doc.name}</p>
				<p><strong>Amount:</strong> {frappe.format_value(doc.amount, {'fieldtype': 'Currency'})}</p>
				<p><strong>Status:</strong> {doc.status}</p>
				<p><strong>Estimated Processing Time:</strong> 48 hours</p>
				<p>You will receive an email notification once the request is reviewed.</p>
			""",
			now=True
		)
	except Exception as e:
		frappe.log_error(title="Payout Request Notification", message=f"Failed to send payout notification: {str(e)}")


@frappe.whitelist()
def approve_payout(payout_request_name, notes=None):
	"""Approve a payout request"""
	if not frappe.has_permission("Payout Request", "write"):
		frappe.throw("Insufficient permissions to approve payout requests")
	
	doc = frappe.get_doc("Payout Request", payout_request_name)
	doc.status = "Approved"
	doc.approved_by = frappe.session.user
	doc.approval_date = now_datetime()
	
	if notes:
		doc.processing_notes = notes
	
	doc.save()
	
	return {
		"message": "Payout request approved",
		"request_id": doc.name,
		"status": doc.status
	}


@frappe.whitelist()
def mark_as_paid(payout_request_name, transaction_reference, notes=None):
	"""Mark payout request as paid"""
	if not frappe.has_permission("Payout Request", "write"):
		frappe.throw("Insufficient permissions to mark payout as paid")
	
	doc = frappe.get_doc("Payout Request", payout_request_name)
	doc.status = "Paid"
	doc.processed_date = now_datetime()
	doc.transaction_reference = transaction_reference
	
	if notes:
		doc.processing_notes = notes
	
	doc.save()
	
	# Send notification
	user_email = frappe.db.get_value("User", doc.sales_agent, "email")
	frappe.sendmail(
		recipients=[user_email],
		subject=f"Payout Request {doc.name} Completed",
		message=f"""
			<p>Your payout request has been processed and paid.</p>
			<p><strong>Request ID:</strong> {doc.name}</p>
			<p><strong>Amount:</strong> {frappe.format_value(doc.amount, {'fieldtype': 'Currency'})}</p>
			<p><strong>Transaction Reference:</strong> {transaction_reference}</p>
		""",
		now=True
	)
	
	return {
		"message": "Payout marked as paid",
		"request_id": doc.name,
		"status": doc.status
	}
