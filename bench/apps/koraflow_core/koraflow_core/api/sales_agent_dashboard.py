# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.utils import getdate, add_months, get_first_day, get_last_day, today
from datetime import datetime


@frappe.whitelist()
def get_dashboard_data():
	"""Get comprehensive dashboard data for Sales Agent"""
	user = frappe.session.user
	agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	
	if not agent:
		return {"message": "No Sales Agent profile found for this user."}
	
	# Get referrals
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": agent},
		fields=[
			"name",
			"referral_id",
			"patient_first_name",
			"patient_last_name",
			"patient_name_display",
			"referral_date",
			"current_journey_status",
			"last_status_update",
			"assigned_sales_team_member"
		],
		order_by="referral_date desc",
		limit=10
	)
	
	# Get commission summary
	commission_summary = get_commission_summary(agent)
	
	# Get recent messages
	messages = frappe.get_all(
		"Referral Message",
		filters={"from_user": agent},
		or_filters=[{"to_user": agent}],
		fields=["name", "referral", "subject", "status", "created_at", "from_user", "to_user"],
		order_by="created_at desc",
		limit=5
	)
	
	# Get status distribution
	status_distribution = get_status_distribution(agent)
	
	# Check for banking details
	bank_details_configured = frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user})
	
	return {
		"agent": {
			"name": agent,
			"bank_details_configured": bool(bank_details_configured)
		},
		"referrals": referrals,
		"commission_summary": commission_summary,
		"messages": messages,
		"status_distribution": status_distribution
	}


@frappe.whitelist()
def get_commission_summary(agent=None):
	"""Get commission KPIs for dashboard"""
	if not agent:
		user = frappe.session.user
		agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	
	# Get all commission records (Sales Agent Accrual)
	commissions = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": agent},
		fields=["accrued_amount", "status", "modified", "creation"]
	)
	
	# Calculate totals
	# Status: Accrued, Requested, Paid
	total_earned = sum(c.accrued_amount or 0 for c in commissions if c.status == "Paid")
	pending = sum(c.accrued_amount or 0 for c in commissions if c.status in ["Accrued", "Requested"])
	paid = sum(c.accrued_amount or 0 for c in commissions if c.status == "Paid")
	
	# This month vs last month
	today = getdate()
	first_day_this_month = get_first_day(today)
	last_day_this_month = get_last_day(today)
	first_day_last_month = get_first_day(add_months(today, -1))
	last_day_last_month = get_last_day(add_months(today, -1))
	
	this_month = sum(
		c.accrued_amount or 0 
		for c in commissions 
		if c.status == "Paid" 
		and c.modified 
		and first_day_this_month <= getdate(c.modified) <= last_day_this_month
	)
	
	last_month = sum(
		c.accrued_amount or 0 
		for c in commissions 
		if c.status == "Paid" 
		and c.modified 
		and first_day_last_month <= getdate(c.modified) <= last_day_last_month
	)
	
	# Calculate percentage change
	if last_month > 0:
		month_change = ((this_month - last_month) / last_month) * 100
	else:
		month_change = 100 if this_month > 0 else 0
	
	return {
		"total_earned": total_earned,
		"pending": pending,
		"paid": paid,
		"this_month": this_month,
		"last_month": last_month,
		"month_change": round(month_change, 2)
	}


@frappe.whitelist()
def get_status_distribution(agent=None):
	"""Get distribution of referral statuses"""
	if not agent:
		user = frappe.session.user
		agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": agent},
		fields=["current_journey_status"]
	)
	
	status_counts = {}
	for ref in referrals:
		status = ref.current_journey_status or "Unknown"
		status_counts[status] = status_counts.get(status, 0) + 1
	
	return status_counts


@frappe.whitelist()
def get_referral_timeline(referral):
	"""Get timeline of status changes for a referral"""
	if not referral:
		return []
	
	# Get version history
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Patient Referral", "docname": referral},
		fields=["name", "creation", "data"],
		order_by="creation desc"
	)
	
	timeline = []
	for version in versions:
		try:
			import json
			data = json.loads(version.data)
			if "changed" in data:
				for change in data["changed"]:
					if change[0] == "current_journey_status":
						timeline.append({
							"status": change[2],
							"date": version.creation,
							"previous": change[1] if len(change) > 1 else None
						})
		except:
			pass
	
	# Also get current status
	referral_doc = frappe.get_doc("Patient Referral", referral)
	if referral_doc.current_journey_status:
		timeline.append({
			"status": referral_doc.current_journey_status,
			"date": referral_doc.last_status_update or referral_doc.modified,
			"current": True
		})
	
	# Sort by date
	timeline.sort(key=lambda x: x.get("date", ""), reverse=True)
	

	return timeline



@frappe.whitelist()
def get_profile_data():
	"""Get Sales Agent profile and banking details"""
	user = frappe.session.user
	if user == "Guest":
		return {"error": "Not logged in"}
	
	agent_name = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not agent_name:
		return {"error": "Sales Agent not found"}
	
	agent = frappe.get_doc("Sales Agent", agent_name)
	
	# Fetch banking details if they exist in the structured DocType
	# Note: Sales Agent Bank Details links to User via 'sales_agent' field
	bank_details = {}
	if frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user}):
		bank_doc_name = frappe.db.get_value("Sales Agent Bank Details", {"sales_agent": user}, "name")
		bank_doc = frappe.get_doc("Sales Agent Bank Details", bank_doc_name)
		bank_details = {
			"bank_name": bank_doc.bank_name,
			"account_holder_name": bank_doc.account_holder_name,
			"account_number": bank_doc.account_number, # Will be masked often, but for edit we might need it if strict permission allows
			"branch_code": bank_doc.branch_code,
			"account_type": bank_doc.account_type,
			"account_number_masked": bank_doc.account_number_masked,
			"proof_of_account": bank_doc.proof_of_account
		}
	else:
		# Fallback to legacy text field if structured data not found
		if agent.bank_details:
			parts = agent.bank_details.split('\n')
			if len(parts) >= 1: bank_details["bank_name"] = parts[0]
			if len(parts) >= 2: bank_details["account_holder_name"] = parts[1]
			if len(parts) >= 3: bank_details["account_number"] = parts[2]
			if len(parts) >= 4: bank_details["branch_code"] = parts[3]
			if len(parts) >= 5: bank_details["account_type"] = parts[4]
	
	# Check if banking details exist for user
	bank_details_configured = frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user})
	
	return {
		"agent": {
			"name": f"{agent.first_name} {agent.last_name}",
			"id": agent.name, # Or ID number
			"bank_details_configured": bool(bank_details_configured)
		},
		"personal_info": {
			"first_name": agent.first_name,
			"last_name": agent.last_name,
			"email": frappe.db.get_value("User", user, "email"),
			"mobile_no": frappe.db.get_value("User", user, "mobile_no")
		},
		"bank_details": bank_details
	}

@frappe.whitelist()
def update_profile_data(bank_name, account_holder_name, account_number, branch_code, account_type, proof_of_account=None):
	"""Update Sales Agent Bank Details"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))
		
	agent_name = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not agent_name:
		frappe.throw(_("Sales Agent not found"))
	
	# Validate inputs
	if not all([bank_name, account_holder_name, account_number, branch_code, account_type]):
		frappe.throw(_("All banking fields are required"))
		
	# Check if record exists
	if frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user}):
		doc_name = frappe.db.get_value("Sales Agent Bank Details", {"sales_agent": user}, "name")
		doc = frappe.get_doc("Sales Agent Bank Details", doc_name)
		doc.bank_name = bank_name
		doc.account_holder_name = account_holder_name
		doc.account_number = account_number
		doc.branch_code = branch_code
		doc.account_type = account_type
		if proof_of_account:
			doc.proof_of_account = proof_of_account
		doc.save(ignore_permissions=True)
	else:
		# Create new
		doc = frappe.get_doc({
			"doctype": "Sales Agent Bank Details",
			"sales_agent": user,
			"bank_name": bank_name,
			"account_holder_name": account_holder_name,
			"account_number": account_number,
			"branch_code": branch_code,
			"account_type": account_type,
			"proof_of_account": proof_of_account
		})
		doc.insert(ignore_permissions=True)
		
	# Also update the legacy text field on Sales Agent for backward compatibility
	agent = frappe.get_doc("Sales Agent", agent_name)
	legacy_details = f"{bank_name}\n{account_holder_name}\n{account_number}\n{branch_code}\n{account_type}"
	agent.bank_details = legacy_details
	agent.save(ignore_permissions=True)
		
	return {"message": "Banking details updated successfully"}


@frappe.whitelist()
def create_referral(first_name, last_name, email, mobile_no):
	"""Create a new referral (and patient if needed)"""
	agent = frappe.session.user
	if agent == "Guest":
		frappe.throw(_("Not logged in"))
		
	# Check for existing patient by email
	patient_name = None
	if frappe.db.exists("Patient", {"email": email}):
		patient_name = frappe.db.get_value("Patient", {"email": email}, "name")
	else:
		# Create new Patient
		# We use minimal fields as per plan
		p = frappe.get_doc({
			"doctype": "Patient",
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"mobile": mobile_no,
			"sex": "Female", # Defaulting as per common flow
			"referred_by_sales_agent": frappe.db.get_value("Sales Agent", {"user": agent}, "name")
		})
		p.insert(ignore_permissions=True)
		patient_name = p.name
		
	# Create Referral
	referral = frappe.get_doc({
		"doctype": "Patient Referral",
		"sales_agent": agent,
		"patient": patient_name,
		"patient_first_name": first_name,
		"patient_last_name": last_name,
		"referral_date": today(),
		"current_journey_status": "Lead Received"
	})
	referral.insert(ignore_permissions=True)
	
	return {"message": "Referral created successfully", "referral": referral.name}
