import frappe
from frappe import _
from frappe.utils import getdate

def on_invoice_paid(doc, method):
	"""
	Triggered when Sales Invoice is paid.
	Calculates commission/marketing fee for the Sales Agent if the patient was referred.
	"""
	if doc.status != "Paid":
		return

	if not doc.patient:
		return

	# Fetch patient's sales agent from Patient Referral
	# Patient Referral 'sales_agent' field is a link to User (email)
	sales_agent_user = frappe.db.get_value("Patient Referral", 
		{"patient": doc.patient, "status": ["!=", "Cancelled"]}, 
		"sales_agent")
	
	sales_agent = None
	if sales_agent_user:
		sales_agent = frappe.db.get_value("Sales Agent", {"user": sales_agent_user}, "name")

	if not sales_agent:
		# Fallback: Check if field exists on Patient (legacy support or direct link)
		if frappe.db.has_column("Patient", "referred_by_sales_agent"):
			sales_agent = frappe.db.get_value("Patient", doc.patient, "referred_by_sales_agent")
	
	if not sales_agent:
		return
	
	agent_doc = frappe.get_doc("Sales Agent", sales_agent)
	if agent_doc.status != "Active":
		return

	# Check if Accrual already exists for this invoice to prevent duplicates
	if frappe.db.exists("Sales Agent Accrual", {"invoice_reference": doc.name, "sales_agent": sales_agent}):
		return

	accruals_created = False

	for item in doc.items:
		commission_amount = 0
		rule_found = False
		
		# 1. Look for Specific Rule for Agent + Item
		rule = frappe.db.get_value("Sales Agent Commission Rule", 
			{"sales_agent": sales_agent, "item": item.item_code, "valid_from": ["<=", doc.posting_date], "valid_to": [">=", doc.posting_date]}, 
			["commission_type", "value"], as_dict=True)
		
		# 2. Look for Specific Rule for Agent + Item Group
		if not rule:
			rule = frappe.db.get_value("Sales Agent Commission Rule", 
				{"sales_agent": sales_agent, "item_group": item.item_group, "valid_from": ["<=", doc.posting_date], "valid_to": [">=", doc.posting_date]}, 
				["commission_type", "value"], as_dict=True)
				
		# 3. Look for Global Rule for Item (No Agent specified)
		if not rule:
			rule = frappe.db.get_value("Sales Agent Commission Rule", 
				{"sales_agent": ["is", "not set"], "item": item.item_code, "valid_from": ["<=", doc.posting_date], "valid_to": [">=", doc.posting_date]}, 
				["commission_type", "value"], as_dict=True)

		# 4. Look for Global Rule for Item Group (No Agent specified)
		if not rule:
			rule = frappe.db.get_value("Sales Agent Commission Rule", 
				{"sales_agent": ["is", "not set"], "item_group": item.item_group, "valid_from": ["<=", doc.posting_date], "valid_to": [">=", doc.posting_date]}, 
				["commission_type", "value"], as_dict=True)
		
		# Fallback to Agent's default commission rate if no rule found
		if rule:
			if rule.commission_type == "Percentage":
				commission_amount = item.amount * (rule.value / 100.0)
			else:
				commission_amount = rule.value * item.qty
		elif agent_doc.commission_rate > 0:
			commission_amount = item.amount * (agent_doc.commission_rate / 100.0)

		if commission_amount > 0:
			accrual = frappe.get_doc({
				"doctype": "Sales Agent Accrual",
				"sales_agent": sales_agent,
				"patient": doc.patient,
				"invoice_reference": doc.name,
				"item_code": item.item_code,
				"accrued_amount": commission_amount,
				"status": "Accrued"
			})
			accrual.insert(ignore_permissions=True)
			accruals_created = True

	if accruals_created:
		frappe.logger().info(f"Marketing fees accrued for Sales Agent: {sales_agent} on Invoice {doc.name}")

