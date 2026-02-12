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

	if not doc.get("patient"):
		return

	# Fetch patient's sales agent from Patient Referral
	# Patient Referral 'sales_agent' field is a link to User (email)
	sales_agent_user = frappe.db.get_value("Patient Referral", 
		{"patient": doc.patient, "current_journey_status": ["!=", "Cancelled"]}, 
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
		
		# Helper to find matching rule
		def get_matching_rule(agent, item_code, item_group, date):
			# Fetch all potentially matching rules
			filters = {
				"valid_from": ["<=", date]
			}
			# We can't easily do OR condition for valid_to in simple filter (valid_to >= date OR valid_to is None)
			# So we fetch matches on Agent/Item and filter dates in Python
			
			or_filters = []
			
			# Priority 1: Agent + Item
			rules = frappe.get_all("Sales Agent Commission Rule", 
				filters={"sales_agent": agent, "item": item_code, "valid_from": ["<=", date]}, 
				fields=["name", "commission_type", "value", "valid_to"])
			
			# Filter by valid_to
			valid_rule = next((r for r in rules if not r.valid_to or getdate(r.valid_to) >= getdate(date)), None)
			if valid_rule: return valid_rule

			# Priority 2: Agent + Item Group
			rules = frappe.get_all("Sales Agent Commission Rule", 
				filters={"sales_agent": agent, "item_group": item_group, "valid_from": ["<=", date]}, 
				fields=["name", "commission_type", "value", "valid_to"])
			valid_rule = next((r for r in rules if not r.valid_to or getdate(r.valid_to) >= getdate(date)), None)
			if valid_rule: return valid_rule

			# Priority 3: Global + Item
			# sales_agent IS NULL or specific string "not set"? 
			# In DB, empty link is NULL or ''.
			# We'll try both or assume standard empty.
			rules = frappe.get_all("Sales Agent Commission Rule", 
				filters={"item": item_code, "valid_from": ["<=", date]}, 
				fields=["name", "commission_type", "value", "valid_to", "sales_agent"])
			valid_rule = next((r for r in rules if (not r.sales_agent) and (not r.valid_to or getdate(r.valid_to) >= getdate(date))), None)
			if valid_rule: return valid_rule

			# Priority 4: Global + Item Group
			rules = frappe.get_all("Sales Agent Commission Rule", 
				filters={"item_group": item_group, "valid_from": ["<=", date]}, 
				fields=["name", "commission_type", "value", "valid_to", "sales_agent"])
			valid_rule = next((r for r in rules if (not r.sales_agent) and (not r.valid_to or getdate(r.valid_to) >= getdate(date))), None)
			if valid_rule: return valid_rule

			return None

		rule = get_matching_rule(sales_agent, item.item_code, item.item_group, doc.posting_date)
		
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

