# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.utils import getdate, add_months, get_first_day, get_last_day
from datetime import datetime


@frappe.whitelist()
def get_dashboard_data():
	"""Get comprehensive dashboard data for Sales Agent"""
	agent = frappe.session.user
	
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
	
	return {
		"referrals": referrals,
		"commission_summary": commission_summary,
		"messages": messages,
		"status_distribution": status_distribution
	}


@frappe.whitelist()
def get_commission_summary(agent=None):
	"""Get commission KPIs for dashboard"""
	if not agent:
		agent = frappe.session.user
	
	# Get all commission records
	commissions = frappe.get_all(
		"Commission Record",
		filters={"sales_agent": agent},
		fields=["commission_amount", "commission_status", "paid_date", "referral_date"]
	)
	
	# Calculate totals
	total_earned = sum(c.commission_amount or 0 for c in commissions if c.commission_status == "Paid")
	pending = sum(c.commission_amount or 0 for c in commissions if c.commission_status in ["Pending", "Approved"])
	paid = sum(c.commission_amount or 0 for c in commissions if c.commission_status == "Paid")
	
	# This month vs last month
	today = getdate()
	first_day_this_month = get_first_day(today)
	last_day_this_month = get_last_day(today)
	first_day_last_month = get_first_day(add_months(today, -1))
	last_day_last_month = get_last_day(add_months(today, -1))
	
	this_month = sum(
		c.commission_amount or 0 
		for c in commissions 
		if c.commission_status == "Paid" 
		and c.paid_date 
		and first_day_this_month <= getdate(c.paid_date) <= last_day_this_month
	)
	
	last_month = sum(
		c.commission_amount or 0 
		for c in commissions 
		if c.commission_status == "Paid" 
		and c.paid_date 
		and first_day_last_month <= getdate(c.paid_date) <= last_day_last_month
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
		agent = frappe.session.user
	
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

