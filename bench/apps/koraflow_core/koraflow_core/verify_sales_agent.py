import frappe
from frappe.utils import today, add_days

def execute():
	frappe.db.rollback() # Start clean transaction for testing

	# Helper to register DocType if missing (Simulate migrate)
	def register_doctype(doctype, module):
		if not frappe.db.exists("DocType", doctype):
			d = frappe.new_doc("DocType")
			d.name = doctype
			d.module = module
			d.custom = 1 # Mark as custom to avoid some strict checks or just insert
			# We ideally load from file, but minimal fields usually suffix for controller loading
			# unless fields are accessed.
			# Better: Load from json file
			import json
			import os
			from frappe.modules import scrub
			try:
				# Use relative path from this script
				base_path = os.path.dirname(__file__)
				path = os.path.join(base_path, "doctype", scrub(doctype), scrub(doctype) + ".json")
				
				# If not found, try standard module path just in case
				if not os.path.exists(path):
				    from frappe.modules import get_module_path
				    path = os.path.join(get_module_path(module), "doctype", scrub(doctype), scrub(doctype) + ".json")

				with open(path, "r") as f:
					doc_data = json.load(f)
					d.update(doc_data)
					d.insert(ignore_permissions=True)
			except Exception as e:
				print(f"Failed to register {doctype}: {str(e)}")

	register_doctype("Sales Agent Commission Rule", "Koraflow Core")
	register_doctype("Sales Agent Commission Rule", "Koraflow Core")
	register_doctype("Sales Agent Payout Request", "Koraflow Core")

	# Ensure Module Def exists for correct controller loading
	if not frappe.db.exists("Module Def", "Koraflow Core"):
		m = frappe.new_doc("Module Def")
		m.module_name = "Koraflow Core"
		m.app_name = "koraflow_core"
		m.insert(ignore_permissions=True)


	try:
		# 1. Setup Sales Agent
		user = "test.agent@example.com"
		if not frappe.db.exists("User", user):
			u = frappe.new_doc("User")
			u.email = user
			u.first_name = "Test"
			u.last_name = "Agent"
			u.insert(ignore_permissions=True)
		
		agent_name = "Test Agent"
		if not frappe.db.exists("Sales Agent", {"user": user}):
			sa = frappe.new_doc("Sales Agent")
			sa.first_name = "Test"
			sa.last_name = "Agent"
			sa.user = user
			sa.status = "Active"
			sa.commission_rate = 10 # Default 10%
			sa.insert(ignore_permissions=True)
			agent_name = sa.name
		else:
			agent_name = frappe.db.get_value("Sales Agent", {"user": user}, "name")

		print(f"Sales Agent Created: {agent_name}")

		# 2. Setup Patient
		patient_name = "Referral Patient"
		if not frappe.db.exists("Patient", {"first_name": "Referral"}):
			p = frappe.new_doc("Patient")
			p.first_name = "Referral"
			p.last_name = "Patient"
			p.sex = "Male"
			p.referred_by_sales_agent = agent_name
			p.insert(ignore_permissions=True)
			patient_name = p.name
		else:
			patient_name = frappe.db.get_value("Patient", {"first_name": "Referral"}, "name")
		
		# Create/Ensure Patient Referral exists
		if not frappe.db.exists("Patient Referral", {"patient": patient_name, "sales_agent": user}):
			pr = frappe.new_doc("Patient Referral")
			pr.patient = patient_name
			pr.sales_agent = user # Link to User
			pr.patient_first_name = "Referral"
			pr.patient_last_name = "Patient"
			pr.status = "Active"
			pr.referral_date = today()
			pr.current_journey_status = "Invoice Paid" # Simulate status
			pr.insert(ignore_permissions=True)


		# 3. Create Item and Commission Rule
		item_code = "Test Item GLP1"
		if not frappe.db.exists("Item", item_code):
			i = frappe.new_doc("Item")
			i.item_code = item_code
			i.item_group = "Products"
			i.is_sales_item = 1
			i.insert(ignore_permissions=True)
		
		# Rule: 20% for this item (Overrides default 10%)
		rule_name = "GLP1 20%"
		if not frappe.db.exists("Sales Agent Commission Rule", {"rule_name": rule_name}):
			rule = frappe.new_doc("Sales Agent Commission Rule")
			rule.rule_name = rule_name
			rule.item = item_code
			rule.sales_agent = agent_name # Specific to this agent
			rule.commission_type = "Percentage"
			rule.value = 20
			rule.valid_from = today()
			rule.insert(ignore_permissions=True)

		# 4. Create and Pay Sales Invoice
		si = frappe.new_doc("Sales Invoice")
		si.customer = "Test Customer" # Assuming exists or creates generic
		if not frappe.db.exists("Customer", "Test Customer"):
			c = frappe.new_doc("Customer")
			c.customer_name = "Test Customer"
			c.insert(ignore_permissions=True)
			
		si.customer = "Test Customer"
		si.patient = patient_name
		si.append("items", {
			"item_code": item_code,
			"qty": 1,
			"rate": 1000
		})
		si.insert(ignore_permissions=True)
		si.submit()
		
		# Pay it
		si.db_set("status", "Paid")
		# Manually trigger hook because db_set doesn't trigger events?
		# Correct, db_set skips. `on_submit` usually sets status to Unpaid. `make_payment_entry` clears it.
		# For test, manually call hook.
		from koraflow_core.hooks.commission_hooks import on_invoice_paid
		on_invoice_paid(si, "on_submit") 

		# 5. Check Accrual
		accruals = frappe.get_all("Sales Agent Accrual", filters={"invoice_reference": si.name, "sales_agent": agent_name}, fields=["accrued_amount"])
		
		if not accruals:
			print("FAILED: No Accrual Created")
		else:
			amount = accruals[0].accrued_amount
			print(f"Accrual Created: {amount}")
			if amount == 200.0:
				print("SUCCESS: Commission calculated correctly (20% of 1000)")
			else:
				print(f"FAILED: Expected 200.0, got {amount}")

		# 6. Request Payout (mocking session user)
		# We can just call the Payout Request creation logic directly or via API function
		from koraflow_core.api.agent_portal import request_payout
		
		# Mock session
		frappe.session.user = user
		
		# Request full amount
		res = request_payout(200.0)
		print(f"Payout Request Result: {res}")

		# Submit the PR (API does it, but check status)
		pr_name = res.get("name")
		pr = frappe.get_doc("Sales Agent Payout Request", pr_name)
		
		print(f"Payout Request: {pr.name}, Status: {pr.status}, Docstatus: {pr.docstatus}")
		print(f"Controller Class: {type(pr)}")
		print(f"Generated Invoice: {pr.generated_invoice}")

		# Manual controller invocation to workaround test env issues
		if pr.status != "Approved":
			try:
				print("Attempting manual invoice creation via Controller logic...")
				from koraflow_core.doctype.sales_agent_payout_request.sales_agent_payout_request import SalesAgentPayoutRequest
				SalesAgentPayoutRequest.create_purchase_invoice(pr)
				pr.reload()
				print(f"Post-Manual Invoke Status: {pr.status}, Invoice: {pr.generated_invoice}")
			except Exception as e:
				print(f"Manual Invoke Failed: {e}")

		if pr.status == "Approved" and pr.generated_invoice:
			print(f"SUCCESS: Payout Request {pr.name} Created and Approved.")
			print(f"Generated Invoice: {pr.generated_invoice}")
		else:
			print(f"PARTIAL/Review Needed: Payout Request {pr.name} Status: {pr.status}")

	except Exception as e:
		print(f"ERROR: {str(e)}")
		import traceback
		traceback.print_exc()

	finally:
		frappe.db.rollback() # Cleanup

