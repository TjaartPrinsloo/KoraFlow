# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.utils import getdate, add_months, get_first_day, get_last_day, today
from datetime import datetime


def _build_patient_pipeline(agent, user):
	"""Build referral pipeline entries from patients linked via custom_ref_sales_partner.

	Determines each patient's journey status by checking their quotation/invoice state.
	"""
	from frappe.utils import formatdate

	patients = frappe.get_all(
		"Patient",
		filters={"custom_ref_sales_partner": agent},
		fields=["name", "first_name", "last_name", "creation"],
	)

	pipeline = []
	for p in patients:
		# Determine status by checking invoices then quotations
		status = "Lead Received"

		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"patient": p.name, "docstatus": 1},
			fields=["name", "status", "grand_total"],
			order_by="posting_date desc",
			limit=1,
		)

		if invoices:
			inv = invoices[0]
			if inv.status == "Paid":
				status = "Invoice Paid"
			elif inv.status in ("Unpaid", "Overdue"):
				status = "Awaiting Payment"
			else:
				status = "Invoice Created"
		else:
			quotations = frappe.get_all(
				"Quotation",
				filters={"party_name": p.name},
				fields=["name", "status"],
				order_by="transaction_date desc",
				limit=1,
			)
			if quotations:
				q = quotations[0]
				if q.status == "Ordered":
					status = "Quote Accepted"
				elif q.status in ("Open", "Draft"):
					status = "Quoted"
				elif q.status == "Lost":
					status = "Quote Declined"
				else:
					status = "Quoted"
			else:
				# Patient exists but no quote yet
				status = "Intake Complete"

		# Mask patient name: "Test P."
		masked = f"{p.first_name} {(p.last_name or '')[0]}." if p.last_name else p.first_name

		pipeline.append({
			"name": p.name,
			"referral_id": "",
			"patient_first_name": p.first_name,
			"patient_last_name": p.last_name,
			"patient_name_display": masked,
			"referral_date": str(p.creation.date()) if p.creation else "",
			"current_journey_status": status,
			"last_status_update": "",
			"assigned_sales_team_member": "",
		})

	return pipeline


@frappe.whitelist(allow_guest=True)
def get_dashboard_data():
	"""Get comprehensive dashboard data for Sales Agent"""
	user = frappe.session.user
	agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	
	if not agent:
		return {"message": "No Sales Agent profile found for this user."}
	
	# Get referrals from Patient Referral doctype
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": user},
		fields=[
			"name",
			"referral_id",
			"patient",
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

	# Also build pipeline from patients linked via Sales Partner
	# This catches patients referred through custom_ref_sales_partner
	pipeline = _build_patient_pipeline(agent, user)
	# Build lookup of dynamically computed statuses by patient ID
	pipeline_status_by_patient = {
		e.get("name"): e.get("current_journey_status")
		for e in pipeline if e.get("name")
	}
	# Update stale Patient Referral statuses with dynamically computed ones
	referral_patient_names = set()
	for r in referrals:
		patient_id = r.get("patient")
		if patient_id and patient_id in pipeline_status_by_patient:
			r["current_journey_status"] = pipeline_status_by_patient[patient_id]
		referral_patient_names.add(r.get("patient_first_name", "") + " " + r.get("patient_last_name", ""))
	# Add pipeline entries that aren't already in referrals
	for entry in pipeline:
		display = entry.get("patient_name_display", "")
		if display not in referral_patient_names:
			referrals.append(entry)

	# Sort combined list by date descending
	referrals.sort(key=lambda r: str(r.get("referral_date") or ""), reverse=True)
	
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
	
	# Get KPI Stats
	kpi_stats = get_kpi_stats(agent)
	
	# Get Commission History with user-friendly display status
	commission_history = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": agent},
		fields=["name", "creation", "accrued_amount", "status", "invoice_reference"],
		order_by="creation desc",
		limit=10
	)

	# Calculate how much has been paid out to determine display status
	paid_payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": agent, "status": "Paid", "docstatus": 1},
		fields=["amount"]
	)
	total_paid_out = sum(p.amount or 0 for p in paid_payouts)

	pending_payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": agent, "status": ["in", ["Pending", "Approved"]], "docstatus": 1},
		fields=["amount"]
	)
	total_pending_payout = sum(p.amount or 0 for p in pending_payouts)

	# Walk accruals in FIFO order to assign display status
	accruals_fifo = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": agent},
		fields=["name", "accrued_amount"],
		order_by="creation asc"
	)
	display_status_map = {}
	paid_remaining = total_paid_out
	pending_remaining = total_pending_payout
	for acc in accruals_fifo:
		amt = acc.accrued_amount or 0
		if paid_remaining >= amt:
			display_status_map[acc.name] = "Paid Out"
			paid_remaining -= amt
		elif pending_remaining > 0:
			display_status_map[acc.name] = "Payout Requested"
			pending_remaining -= amt
		else:
			display_status_map[acc.name] = "In Wallet"

	for comm in commission_history:
		comm["display_status"] = display_status_map.get(comm.name, "In Wallet")
	
	# Check for banking details
	bank_details_configured = frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user})
	
	return {
		"agent": {
			"name": agent,
			"bank_details_configured": bool(bank_details_configured)
		},
		"referrals": referrals,
		"commission_summary": commission_summary,
		"commission_history": commission_history,
		"kpi_stats": kpi_stats,
		"messages": messages,
		"status_distribution": status_distribution
	}


@frappe.whitelist(allow_guest=True)
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
	total_earned = sum(c.accrued_amount or 0 for c in commissions)
	total_accrued_and_requested = sum(
		c.accrued_amount or 0 for c in commissions if c.status in ["Accrued", "Requested"]
	)
	paid = sum(c.accrued_amount or 0 for c in commissions if c.status == "Paid")

	# Available = total unpaid commissions minus pending/approved payout requests
	pending_payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": agent, "status": ["in", ["Pending", "Approved"]], "docstatus": 1},
		fields=["amount"]
	)
	total_pending_payouts = sum(p.amount or 0 for p in pending_payouts)
	available = max(total_accrued_and_requested - total_pending_payouts, 0)
	pending = total_accrued_and_requested
	
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
		"available": available,
		"pending": pending,
		"paid": paid,
		"this_month": this_month,
		"last_month": last_month,
		"month_change": round(month_change, 2)
	}


@frappe.whitelist(allow_guest=True)
def get_status_distribution(agent=None):
	"""Get distribution of referral statuses (from both Patient Referral and Sales Partner patients)"""
	if not agent:
		user = frappe.session.user
		agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")

	user = frappe.db.get_value("Sales Agent", agent, "user") or frappe.session.user

	# From Patient Referral
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": user},
		fields=["current_journey_status"]
	)

	status_counts = {}
	for ref in referrals:
		status = ref.current_journey_status or "Unknown"
		status_counts[status] = status_counts.get(status, 0) + 1

	# Also include pipeline patients
	pipeline = _build_patient_pipeline(agent, user)
	for entry in pipeline:
		status = entry.get("current_journey_status", "Unknown")
		status_counts[status] = status_counts.get(status, 0) + 1

	return status_counts


@frappe.whitelist(allow_guest=True)
def get_referral_timeline(referral):
	"""Get timeline of status changes for a referral"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not logged in"))
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



@frappe.whitelist(allow_guest=True)
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
        # Account Number is Password field, so we need to decrypt it to mask it partially
		raw_account_number = bank_doc.get_password("account_number")
		
		bank_details = {
			"bank_name": bank_doc.bank_name,
			"account_holder_name": bank_doc.account_holder_name,
			"account_number": mask_account_number(raw_account_number), # MASKED
			"branch_code": bank_doc.branch_code,
			"account_type": bank_doc.account_type,
			"account_number_masked": mask_account_number(raw_account_number),
			"proof_of_account": bank_doc.proof_of_account
		}
	else:
		# Fallback to legacy text field if structured data not found
		if agent.bank_details:
			parts = agent.bank_details.split('\n')
			if len(parts) >= 1: bank_details["bank_name"] = parts[0]
			if len(parts) >= 2: bank_details["account_holder_name"] = parts[1]
			if len(parts) >= 3: bank_details["account_number"] = mask_account_number(parts[2])
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

def mask_account_number(account_number):
	"""Masks account number, showing only last 4 digits"""
	if not account_number:
		return ""
	if len(account_number) <= 4:
		return "*" * len(account_number)
	return "*" * (len(account_number) - 4) + account_number[-4:]

@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def create_referral(first_name, last_name, email, mobile_no, sex=None, dob=None):
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
			"sex": sex or "Female", # Defaulting as per common flow but allowing override
			"referred_by_sales_agent": frappe.db.get_value("Sales Agent", {"user": agent}, "name")
		})
		if dob:
			p.dob = dob
			
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

@frappe.whitelist(allow_guest=True)
def get_kpi_stats(agent):
	"""Calculate KPI statistics for the agent"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not logged in"))
	user_email = frappe.db.get_value("Sales Agent", agent, "user")

	if not user_email:
		return {
			"total_referrals": 0,
			"conversion_rate": 0,
			"total_patients": 0,
			"avg_ticket": 0
		}

	# Collect patient names from both sources
	referral_patients = frappe.get_all(
		"Patient Referral", filters={"sales_agent": user_email}, pluck="patient"
	)
	partner_patients = frappe.get_all(
		"Patient", filters={"custom_ref_sales_partner": agent}, pluck="name"
	)
	all_patients = list(set(referral_patients + partner_patients))

	total_referrals = len(all_patients)

	# Conversion = patients with a paid invoice
	converted_count = 0
	if all_patients:
		converted_count = frappe.db.count(
			"Sales Invoice",
			{"patient": ["in", all_patients], "status": "Paid", "docstatus": 1},
		)

	conversion_rate = (converted_count / total_referrals * 100) if total_referrals else 0

	total_patients = total_referrals

	# Avg ticket from paid invoices
	avg_ticket = 0
	if all_patients:
		result = frappe.db.sql("""
			SELECT AVG(grand_total)
			FROM `tabSales Invoice`
			WHERE patient IN %(patients)s
			AND status = 'Paid' AND docstatus = 1
		""", {"patients": all_patients})
		if result and result[0][0]:
			avg_ticket = result[0][0]
			
	return {
		"total_referrals": total_referrals,
		"conversion_rate": round(conversion_rate, 1),
		"total_patients": total_patients,
		"avg_ticket": round(avg_ticket, 2)
	}

@frappe.whitelist(allow_guest=True)
def create_support_ticket(subject, description):
    """Create a new support ticket (Issue) for the sales agent"""
    if not subject or not description:
        frappe.throw("Subject and Description are required.")
        
    user = frappe.session.user
    
    issue = frappe.get_doc({
        "doctype": "Issue",
        "subject": subject,
        "raised_by": user,
        "description": description,
        "custom_sales_agent_email": user, # Optional: if we want to track who raised it explicitly in a custom field
        "status": "Open",
        "priority": "Medium",
        "issue_type": "Sales Agent Support" # Adjust if "Issue Type" exists
    })
    
    # Check if Issue Type exists, if not use default or skip
    if not frappe.db.exists("Issue Type", "Sales Agent Support"):
        issue.issue_type = None # Let system default handle it or just leave empty
        
    issue.insert(ignore_permissions=True)
    
    return {"message": "Support ticket created successfully", "issue": issue.name}


def _get_all_patients_for_agent(agent, user):
	"""Get all patient names linked to this agent via both Patient Referral and Sales Partner."""
	referral_patients = frappe.get_all(
		"Patient Referral", filters={"sales_agent": user}, pluck="patient"
	)
	partner_patients = frappe.get_all(
		"Patient", filters={"custom_ref_sales_partner": agent}, pluck="name"
	)
	return list(set(p for p in referral_patients + partner_patients if p))


def _mask_doc_ref(doc_name):
	"""Mask document reference showing only last 4 characters."""
	if not doc_name:
		return ""
	if len(doc_name) <= 4:
		return doc_name
	return "..." + doc_name[-4:]


def _check_reminder_cooldown(patient_referral, hours=48):
	"""Check if a reminder was sent for this referral within the cooldown period."""
	from frappe.utils import add_to_date, now_datetime

	cutoff = add_to_date(now_datetime(), hours=-hours)
	return frappe.db.exists(
		"Referral Message",
		{
			"referral": patient_referral,
			"subject": ["like", "[Reminder]%"],
			"creation": [">=", cutoff],
		},
	)


@frappe.whitelist(allow_guest=True)
def get_crm_data(agent_filter=None):
	"""Get CRM data: outstanding quotes, invoices, and reminder log for the agent's referrals."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))

	is_manager = "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user)

	# Resolve agent
	if agent_filter and is_manager:
		agent = agent_filter
		agent_user = frappe.db.get_value("Sales Agent", agent, "user")
		if not agent_user:
			frappe.throw(_("Sales Agent not found"))
	else:
		agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
		agent_user = user

	if not agent and not is_manager:
		return {"message": "No Sales Agent profile found for this user."}

	# For System Managers without a Sales Agent profile viewing all data
	if not agent and is_manager:
		agent = agent_filter
		if not agent:
			# Return empty with agents list so they can pick one
			agents_list = _get_agents_list()
			return {
				"outstanding_quotes": [],
				"outstanding_invoices": [],
				"crm_stats": {
					"outstanding_quotes_count": 0, "outstanding_quotes_value": 0,
					"overdue_invoices_count": 0, "overdue_invoices_value": 0,
					"reminders_sent_this_month": 0,
				},
				"reminder_log": [],
				"agents_list": agents_list,
			}

	all_patients = _get_all_patients_for_agent(agent, agent_user)

	outstanding_quotes = []
	outstanding_invoices = []

	if all_patients:
		# Get patient details for masking
		patient_details = {
			p.name: p
			for p in frappe.get_all(
				"Patient",
				filters={"name": ["in", all_patients]},
				fields=["name", "first_name", "last_name"],
			)
		}

		# Find the Patient Referral for each patient (for reminder routing)
		referral_map = {}
		referrals = frappe.get_all(
			"Patient Referral",
			filters={"patient": ["in", all_patients], "sales_agent": agent_user},
			fields=["name", "patient"],
		)
		for r in referrals:
			referral_map[r.patient] = r.name

		# Auto-create referrals for partner-linked patients without one
		for patient_name in all_patients:
			if patient_name not in referral_map:
				p = patient_details.get(patient_name, frappe._dict())
				try:
					ref = frappe.get_doc({
						"doctype": "Patient Referral",
						"sales_agent": agent_user,
						"patient": patient_name,
						"patient_first_name": p.first_name or "",
						"patient_last_name": p.last_name or "",
						"referral_date": today(),
						"current_journey_status": "Lead Received",
					})
					ref.insert(ignore_permissions=True)
					referral_map[patient_name] = ref.name
				except Exception:
					pass  # Skip if creation fails

		# Outstanding Quotations (Draft = waiting for patient, Submitted+Open = sent but not accepted)
		quotations = frappe.get_all(
			"Quotation",
			filters={
				"party_name": ["in", all_patients],
				"docstatus": ["in", [0, 1]],
				"status": ["not in", ["Ordered", "Lost", "Cancelled"]],
			},
			fields=["name", "party_name", "status", "grand_total", "transaction_date", "docstatus"],
			order_by="transaction_date desc",
		)

		for q in quotations:
			p = patient_details.get(q.party_name, frappe._dict())
			masked = f"{p.first_name or 'Unknown'} {(p.last_name or ' ')[0]}." if p else "Unknown"
			days = (getdate(today()) - getdate(q.transaction_date)).days if q.transaction_date else 0
			ref_name = referral_map.get(q.party_name)
			can_remind = not _check_reminder_cooldown(ref_name) if ref_name else False

			display_status = "Draft" if q.docstatus == 0 else q.status
			outstanding_quotes.append({
				"masked_name": masked,
				"doc_ref": _mask_doc_ref(q.name),
				"status": display_status,
				"amount": q.grand_total or 0,
				"date": str(q.transaction_date) if q.transaction_date else "",
				"days_outstanding": days,
				"patient_referral": ref_name or "",
				"can_remind": can_remind,
			})

		# Outstanding Sales Invoices
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={
				"patient": ["in", all_patients],
				"docstatus": 1,
				"status": ["in", ["Unpaid", "Overdue"]],
			},
			fields=["name", "patient", "status", "grand_total", "posting_date", "due_date"],
			order_by="posting_date desc",
		)

		for inv in invoices:
			p = patient_details.get(inv.patient, frappe._dict())
			masked = f"{p.first_name or 'Unknown'} {(p.last_name or ' ')[0]}." if p else "Unknown"
			days_overdue = (getdate(today()) - getdate(inv.due_date)).days if inv.due_date else 0
			if days_overdue < 0:
				days_overdue = 0
			ref_name = referral_map.get(inv.patient)
			can_remind = not _check_reminder_cooldown(ref_name) if ref_name else False

			outstanding_invoices.append({
				"masked_name": masked,
				"doc_ref": _mask_doc_ref(inv.name),
				"status": inv.status,
				"amount": inv.grand_total or 0,
				"date": str(inv.posting_date) if inv.posting_date else "",
				"due_date": str(inv.due_date) if inv.due_date else "",
				"days_overdue": days_overdue,
				"patient_referral": ref_name or "",
				"can_remind": can_remind,
			})

	# CRM Stats
	crm_stats = {
		"outstanding_quotes_count": len(outstanding_quotes),
		"outstanding_quotes_value": sum(q["amount"] for q in outstanding_quotes),
		"overdue_invoices_count": len([i for i in outstanding_invoices if i["status"] == "Overdue"]),
		"overdue_invoices_value": sum(i["amount"] for i in outstanding_invoices if i["status"] == "Overdue"),
		"reminders_sent_this_month": 0,
	}

	# Count reminders sent this month
	first_day = get_first_day(getdate(today()))
	if all_patients:
		referral_names = list(referral_map.values())
		if referral_names:
			crm_stats["reminders_sent_this_month"] = frappe.db.count(
				"Referral Message",
				{
					"referral": ["in", referral_names],
					"subject": ["like", "[Reminder]%"],
					"creation": [">=", first_day],
				},
			)

	# Reminder Log (recent 20)
	reminder_log = []
	if all_patients:
		referral_names = list(referral_map.values())
		if referral_names:
			messages = frappe.get_all(
				"Referral Message",
				filters={
					"referral": ["in", referral_names],
					"subject": ["like", "[Reminder]%"],
				},
				fields=["creation", "referral", "subject", "message"],
				order_by="creation desc",
				limit=20,
			)
			for msg in messages:
				# Resolve patient name from referral
				patient_id = frappe.db.get_value("Patient Referral", msg.referral, "patient")
				p = patient_details.get(patient_id, frappe._dict()) if patient_id else frappe._dict()
				masked = f"{p.first_name or 'Unknown'} {(p.last_name or ' ')[0]}." if p.first_name else "Unknown"
				reminder_type = msg.subject.replace("[Reminder] ", "") if msg.subject else "Unknown"

				reminder_log.append({
					"date": str(msg.creation) if msg.creation else "",
					"masked_name": masked,
					"type": reminder_type,
					"channel": "Email",
				})

	result = {
		"outstanding_quotes": outstanding_quotes,
		"outstanding_invoices": outstanding_invoices,
		"crm_stats": crm_stats,
		"reminder_log": reminder_log,
	}

	# Include agents list for System Managers
	if is_manager:
		result["agents_list"] = _get_agents_list()

	return result


def _get_agents_list():
	"""Get list of all active Sales Agents for the admin filter dropdown."""
	agents = frappe.get_all(
		"Sales Agent",
		filters={"status": "Active"},
		fields=["name", "first_name", "last_name"],
		order_by="first_name asc",
	)
	return [
		{"label": f"{a.first_name} {a.last_name}", "value": a.name}
		for a in agents
	]


@frappe.whitelist(allow_guest=True)
def send_patient_reminder(patient_referral, reminder_type):
	"""Send a POPIA-compliant reminder email to a patient and log it."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))

	if reminder_type not in ("quote_pending", "invoice_overdue"):
		frappe.throw(_("Invalid reminder type"))

	# Validate referral exists
	if not frappe.db.exists("Patient Referral", patient_referral):
		frappe.throw(_("Referral not found"))

	referral = frappe.get_doc("Patient Referral", patient_referral)

	# Permission check: must own the referral or be a manager
	is_manager = "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user)
	if referral.sales_agent != user and not is_manager:
		frappe.throw(_("You do not have permission to send reminders for this referral"))

	# Check 48h cooldown
	if _check_reminder_cooldown(patient_referral):
		frappe.throw(_("A reminder was already sent for this patient in the last 48 hours. Please wait before sending another."))

	# Resolve patient details server-side (never exposed to portal)
	patient = frappe.get_doc("Patient", referral.patient)
	patient_email = patient.email
	patient_first_name = patient.first_name or "there"

	if not patient_email:
		frappe.throw(_("No email address found for this patient"))

	# Load POPIA-compliant email templates from Email Template doctype
	template_name = (
		"CRM - Quote Pending Reminder" if reminder_type == "quote_pending"
		else "CRM - Invoice Overdue Reminder"
	)

	template_context = {
		"patient_first_name": patient_first_name,
		"url": frappe.utils.get_url(),
	}

	if frappe.db.exists("Email Template", template_name):
		email_template = frappe.get_doc("Email Template", template_name)
		subject = frappe.render_template(email_template.subject, template_context)
		message = frappe.render_template(email_template.response, template_context)
	else:
		# Fallback if template was deleted
		if reminder_type == "quote_pending":
			subject = "Your Slim2Well Quotation is Waiting"
			message = f"<p>Hi {patient_first_name},</p><p>You have a pending quotation from Slim2Well. Please log in to your portal to review and accept it.</p><p>Kind regards,<br>The Slim2Well Team</p>"
		else:
			subject = "Slim2Well Payment Reminder"
			message = f"<p>Hi {patient_first_name},</p><p>You have an outstanding payment with Slim2Well. Please log in to your portal to complete your payment.</p><p>Kind regards,<br>The Slim2Well Team</p>"

	# Send email
	frappe.sendmail(
		recipients=[patient_email],
		subject=subject,
		message=message,
		now=True,
	)

	# Log as Referral Message for audit trail
	frappe.get_doc({
		"doctype": "Referral Message",
		"referral": patient_referral,
		"from_user": user,
		"to_user": user,
		"subject": f"[Reminder] {reminder_type}",
		"message": f"Automated {reminder_type.replace('_', ' ')} reminder sent via email on {today()}",
		"status": "Read",
	}).insert(ignore_permissions=True)

	# Post comment on Patient Referral (visible in desk timeline)
	reminder_label = "Quote Pending" if reminder_type == "quote_pending" else "Invoice Overdue"
	frappe.get_doc("Patient Referral", patient_referral).add_comment(
		"Comment",
		f"<strong>[Reminder Sent - {reminder_label}]</strong> Email sent to patient"
		f"<br><small>Sent by {user}</small>",
	)

	# Post comment on Patient record too
	if referral.patient:
		frappe.get_doc("Patient", referral.patient).add_comment(
			"Comment",
			f"<strong>Sales Agent Reminder [{reminder_label}]</strong><br>Email reminder sent to patient"
			f"<br><small>Agent: {user} | Ref: {patient_referral}</small>",
		)

	return {"message": "Reminder sent successfully", "reminder_type": reminder_type}


@frappe.whitelist(allow_guest=True)
def log_activity(patient_referral, activity_type, note, followup_date=None):
	"""Log a follow-up activity note against a patient referral."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))

	if not frappe.db.exists("Patient Referral", patient_referral):
		frappe.throw(_("Referral not found"))

	referral = frappe.get_doc("Patient Referral", patient_referral)

	# Permission check
	is_manager = "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user)
	if referral.sales_agent != user and not is_manager:
		frappe.throw(_("You do not have permission to log activities for this referral"))

	if not note or not note.strip():
		frappe.throw(_("Activity note is required"))

	valid_types = ("Call", "WhatsApp", "Email", "Meeting", "Note", "Other")
	if activity_type not in valid_types:
		activity_type = "Note"

	# Log as Referral Message with [Activity] prefix
	frappe.get_doc({
		"doctype": "Referral Message",
		"referral": patient_referral,
		"from_user": user,
		"to_user": user,
		"subject": f"[Activity] {activity_type}",
		"message": note.strip(),
		"status": "Read",
	}).insert(ignore_permissions=True)

	# Post comment on Patient Referral (visible in desk timeline)
	frappe.get_doc("Patient Referral", patient_referral).add_comment(
		"Comment",
		f"<strong>[{activity_type}]</strong> {note.strip()}<br><small>Logged by {user}</small>",
	)

	# Post comment on Patient record too (visible to admins in desk)
	if referral.patient:
		frappe.get_doc("Patient", referral.patient).add_comment(
			"Comment",
			f"<strong>Sales Agent Activity [{activity_type}]</strong><br>{note.strip()}"
			f"<br><small>Agent: {user} | Ref: {patient_referral}</small>",
		)

	# Update follow-up date if provided (use db.set_value to avoid stale doc issues)
	if followup_date:
		frappe.db.set_value("Patient Referral", patient_referral, {
			"next_followup_date": getdate(followup_date),
			"followup_note": note.strip()[:140],
		})
	elif not followup_date and referral.next_followup_date and getdate(referral.next_followup_date) <= getdate(today()):
		frappe.db.set_value("Patient Referral", patient_referral, {
			"next_followup_date": None,
			"followup_note": None,
		})

	return {"message": "Activity logged successfully"}


@frappe.whitelist(allow_guest=True)
def get_patient_activity(patient_referral):
	"""Get the activity timeline for a patient referral."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))

	if not frappe.db.exists("Patient Referral", patient_referral):
		frappe.throw(_("Referral not found"))

	referral = frappe.get_doc("Patient Referral", patient_referral)

	# Permission check
	is_manager = "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user)
	if referral.sales_agent != user and not is_manager:
		frappe.throw(_("You do not have permission to view this referral's activity"))

	# Get all Referral Messages (activities + reminders) for this referral
	messages = frappe.get_all(
		"Referral Message",
		filters={"referral": patient_referral},
		fields=["creation", "from_user", "subject", "message"],
		order_by="creation desc",
		limit=50,
	)

	timeline = []
	for msg in messages:
		# Parse type from subject prefix
		if msg.subject and msg.subject.startswith("[Activity]"):
			entry_type = msg.subject.replace("[Activity] ", "")
			icon = "activity"
		elif msg.subject and msg.subject.startswith("[Reminder]"):
			entry_type = msg.subject.replace("[Reminder] ", "").replace("_", " ").title()
			icon = "reminder"
		else:
			entry_type = "Message"
			icon = "message"

		timeline.append({
			"date": str(msg.creation) if msg.creation else "",
			"type": entry_type,
			"icon": icon,
			"note": msg.message or "",
			"user": msg.from_user,
		})

	# Mask the patient name
	p_first = referral.patient_first_name or "Unknown"
	p_last = referral.patient_last_name or ""
	masked_name = f"{p_first} {p_last[0]}." if p_last else p_first

	return {
		"referral": patient_referral,
		"masked_name": masked_name,
		"current_status": referral.current_journey_status,
		"next_followup_date": str(referral.next_followup_date) if referral.next_followup_date else None,
		"followup_note": referral.followup_note,
		"timeline": timeline,
	}


@frappe.whitelist(allow_guest=True)
def get_followups_due(agent_filter=None):
	"""Get all referrals with upcoming or overdue follow-up dates."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"))

	is_manager = "System Manager" in frappe.get_roles(user) or "Sales Agent Manager" in frappe.get_roles(user)

	# Resolve agent
	if agent_filter and is_manager:
		agent = agent_filter
		agent_user = frappe.db.get_value("Sales Agent", agent, "user")
	else:
		agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
		agent_user = user

	if not agent:
		return {"followups": []}

	# Get all referrals with a follow-up date set
	referrals = frappe.get_all(
		"Patient Referral",
		filters={
			"sales_agent": agent_user,
			"next_followup_date": ["is", "set"],
		},
		fields=[
			"name", "patient_first_name", "patient_last_name",
			"current_journey_status", "next_followup_date", "followup_note",
		],
		order_by="next_followup_date asc",
	)

	# Also get referrals from Sales Partner patients
	partner_patients = frappe.get_all(
		"Patient", filters={"custom_ref_sales_partner": agent}, pluck="name"
	)
	if partner_patients:
		partner_referrals = frappe.get_all(
			"Patient Referral",
			filters={
				"patient": ["in", partner_patients],
				"next_followup_date": ["is", "set"],
			},
			fields=[
				"name", "patient_first_name", "patient_last_name",
				"current_journey_status", "next_followup_date", "followup_note",
			],
			order_by="next_followup_date asc",
		)
		# Merge without duplicates
		existing_names = {r.name for r in referrals}
		for r in partner_referrals:
			if r.name not in existing_names:
				referrals.append(r)

	followups = []
	today_date = getdate(today())

	for ref in referrals:
		fu_date = getdate(ref.next_followup_date)
		days_until = (fu_date - today_date).days
		masked = f"{ref.patient_first_name or 'Unknown'} {(ref.patient_last_name or ' ')[0]}."

		followups.append({
			"referral": ref.name,
			"masked_name": masked,
			"status": ref.current_journey_status,
			"followup_date": str(ref.next_followup_date),
			"followup_note": ref.followup_note or "",
			"days_until": days_until,
			"is_overdue": days_until < 0,
			"is_today": days_until == 0,
		})

	# Sort: overdue first, then today, then upcoming
	followups.sort(key=lambda x: x["followup_date"])

	# Get last activity for each referral (for context)
	for fu in followups:
		last_activity = frappe.get_all(
			"Referral Message",
			filters={
				"referral": fu["referral"],
				"subject": ["like", "[Activity]%"],
			},
			fields=["creation", "message"],
			order_by="creation desc",
			limit=1,
		)
		if last_activity:
			fu["last_activity_date"] = str(last_activity[0].creation)
			fu["last_activity_note"] = (last_activity[0].message or "")[:80]
		else:
			fu["last_activity_date"] = None
			fu["last_activity_note"] = ""

	return {"followups": followups}
