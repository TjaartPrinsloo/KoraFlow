# Copyright (c) 2026, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import random
import string
from datetime import timedelta


class SalesAgentBankDetails(Document):
	def validate(self):
		"""Validate and process bank details before saving"""
		self.mask_account_number()
		self.update_last_modified()
	
	def mask_account_number(self):
		"""Create masked version of account number for display"""
		if self.account_number and not self.account_number_masked:
			# Get the actual account number from password field
			acc_num = self.get_password("account_number")
			if acc_num and len(acc_num) > 4:
				self.account_number_masked = "**** **** " + acc_num[-4:]
	
	def update_last_modified(self):
		"""Update last modified timestamp and IP"""
		self.last_updated = frappe.utils.now()
		if hasattr(frappe.local, 'request_ip'):
			self.updated_by_ip = frappe.local.request_ip


@frappe.whitelist()
def get_bank_details(user=None):
	"""Get masked bank details for a sales agent"""
	if not user:
		user = frappe.session.user
	
	details = frappe.db.get_value(
		"Sales Agent Bank Details",
		{"sales_agent": user},
		["account_holder_name", "bank_name", "account_number_masked", 
		 "account_type", "branch_code", "verification_status"],
		as_dict=True
	)
	
	if not details:
		return {
			"exists": False,
			"verification_status": "Pending"
		}
	
	return {
		"exists": True,
		"account_holder_name": details.account_holder_name,
		"bank_name": details.bank_name,
		"account_number_masked": details.account_number_masked,
		"account_type": details.account_type,
		"branch_code": details.branch_code,
		"verification_status": details.verification_status
	}


@frappe.whitelist()
def request_verification_code():
	"""Generate and send verification code for bank details update"""
	user = frappe.session.user
	email = frappe.db.get_value("User", user, "email")
	
	# Generate 6-digit code
	code = ''.join(random.choices(string.digits, k=6))
	expiry = frappe.utils.add_to_date(frappe.utils.now(), minutes=10)
	
	# Store code temporarily (in session or cache)
	frappe.cache().set_value(
		f"bank_verification_{user}",
		{"code": code, "expiry": expiry},
		expires_in_sec=600  # 10 minutes
	)
	
	# Send email
	try:
		frappe.sendmail(
			recipients=[email],
			subject="Bank Details Verification Code",
			message=f"""
				<p>Your verification code for updating bank details is:</p>
				<h2 style="font-family: monospace; letter-spacing: 0.2em; color: #2563eb;">{code}</h2>
				<p>This code will expire in 10 minutes.</p>
				<p>If you did not request this code, please ignore this email.</p>
			"""
		)
		
		frappe.logger().info(f"Verification code sent to {email}")
		
		return {
			"success": True,
			"message": f"Verification code sent to {email}",
			"expiry": expiry
		}
	except Exception as e:
		frappe.log_error(title="Bank Details Verification", message=f"Failed to send verification email: {str(e)}")
		return {
			"success": False,
			"message": "Failed to send verification code. Please try again."
		}


@frappe.whitelist()
def verify_and_update_bank_details(account_holder_name, bank_name, account_number, 
                                     account_type, branch_code, verification_code):
	"""Verify code and update bank details"""
	user = frappe.session.user
	
	# Get stored verification code
	stored_data = frappe.cache().get_value(f"bank_verification_{user}")
	
	if not stored_data:
		return {
			"success": False,
			"message": "Verification code expired. Please request a new code."
		}
	
	# Check if code matches
	if stored_data["code"] != verification_code:
		return {
			"success": False,
			"message": "Invalid verification code. Please try again."
		}
	
	# Check if code expired
	if frappe.utils.now() > stored_data["expiry"]:
		frappe.cache().delete_value(f"bank_verification_{user}")
		return {
			"success": False,
			"message": "Verification code expired. Please request a new code."
		}
	
	# Code is valid, update bank details
	try:
		# Check if record exists
		existing = frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user})
		
		if existing:
			doc = frappe.get_doc("Sales Agent Bank Details", existing)
		else:
			doc = frappe.get_doc({
				"doctype": "Sales Agent Bank Details",
				"sales_agent": user
			})
		
		# Update fields
		doc.account_holder_name = account_holder_name
		doc.bank_name = bank_name
		doc.account_number = account_number
		doc.account_type = account_type
		doc.branch_code = branch_code
		doc.verification_status = "Verified"
		doc.verification_method = "Email"
		
		if existing:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)
		
		# Clear verification code
		frappe.cache().delete_value(f"bank_verification_{user}")
		
		frappe.logger().info(f"Bank details updated for {user}")
		
		return {
			"success": True,
			"message": "Bank details updated successfully",
			"verification_status": "Verified"
		}
	except Exception as e:
		frappe.log_error(title="Bank Details Update", message=f"Failed to update bank details: {str(e)}")
		return {
			"success": False,
			"message": "Failed to update bank details. Please try again."
		}


@frappe.whitelist()
def get_bank_list():
	"""Get list of South African banks"""
	return [
		"Standard Bank",
		"ABSA",
		"FNB",
		"Nedbank",
		"Capitec",
		"African Bank",
		"Investec",
		"Discovery Bank",
		"TymeBank",
		"Bank Zero"
	]
