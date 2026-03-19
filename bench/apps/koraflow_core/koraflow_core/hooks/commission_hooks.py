import frappe
from frappe import _
from frappe.utils import getdate


def populate_sales_partner(doc, method=None):
	"""Auto-populate sales_partner on Sales Invoice from Patient's linked sales partner."""
	if doc.sales_partner:
		return

	# Resolve patient name — try patient field first, then fall back to customer
	patient_name = doc.get("patient")
	if not patient_name and doc.get("customer"):
		if frappe.db.exists("Patient", doc.customer):
			patient_name = doc.customer

	if not patient_name:
		return

	sales_partner = None
	if frappe.db.has_column("Patient", "custom_ref_sales_partner"):
		sales_partner = frappe.db.get_value("Patient", patient_name, "custom_ref_sales_partner")

	if not sales_partner:
		return

	# Verify the Sales Partner exists
	if not frappe.db.exists("Sales Partner", sales_partner):
		return

	doc.sales_partner = sales_partner

	# Look up commission from Sales Partner Commission Rule for invoice items
	total_commission = 0
	for item in doc.items:
		rule_amount = frappe.db.get_value("Sales Partner Commission Rule",
			{"sales_partner": sales_partner, "item": item.item_code, "enabled": 1},
			"commission_amount")
		if rule_amount:
			total_commission += float(rule_amount) * item.qty

	if total_commission > 0 and doc.grand_total:
		doc.commission_rate = (total_commission / doc.grand_total) * 100
		doc.total_commission = total_commission


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
		# Fallback 1: Check referred_by_sales_agent on Patient
		if frappe.db.has_column("Patient", "referred_by_sales_agent"):
			sales_agent = frappe.db.get_value("Patient", doc.patient, "referred_by_sales_agent")

	if not sales_agent:
		# Fallback 2: Check Sales Partner on Patient → find matching Sales Agent
		sales_partner_field = "custom_ref_sales_partner" if frappe.db.has_column("Patient", "custom_ref_sales_partner") else "custom_sales_partner"
		if frappe.db.has_column("Patient", sales_partner_field):
			sales_partner = frappe.db.get_value("Patient", doc.patient, sales_partner_field)
			if sales_partner:
				# Find Sales Agent linked to this Sales Partner (by matching name)
				sales_agent = frappe.db.get_value("Sales Agent",
					{"first_name": sales_partner.split(" ")[0]}, "name")
				if not sales_agent:
					# Try matching by user email pattern
					partner_user = frappe.db.get_value("Sales Partner", sales_partner, "user")
					if partner_user:
						sales_agent = frappe.db.get_value("Sales Agent", {"user": partner_user}, "name")

	if not sales_agent:
		return

	agent_doc = frappe.get_doc("Sales Agent", sales_agent)

	if agent_doc.status != "Active":
		return

	# Check if Accrual already exists for this invoice to prevent duplicates
	if frappe.db.exists("Sales Agent Accrual", {"invoice_reference": doc.name, "sales_agent": sales_agent}):
		return

	# Resolve the Sales Partner name for commission rule lookup
	sales_partner_name = None
	if frappe.db.has_column("Patient", "custom_ref_sales_partner"):
		sales_partner_name = frappe.db.get_value("Patient", doc.patient, "custom_ref_sales_partner")
	if not sales_partner_name:
		# Try matching agent name to Sales Partner
		sales_partner_name = frappe.db.get_value("Sales Partner", {"name": agent_doc.name}, "name")

	accruals_created = False

	for item in doc.items:
		commission_amount = 0

		# Priority 1: Check Sales Partner Commission Rule (fixed amount per item)
		if sales_partner_name and frappe.db.exists("DocType", "Sales Partner Commission Rule"):
			partner_rule = frappe.db.get_value("Sales Partner Commission Rule",
				{"sales_partner": sales_partner_name, "item": item.item_code, "enabled": 1},
				"commission_amount")
			if partner_rule:
				commission_amount = float(partner_rule) * item.qty

		# Priority 2: Check Sales Agent Commission Rule (percentage or fixed)
		if not commission_amount:
			rule = _get_agent_commission_rule(sales_agent, item.item_code, item.item_group, doc.posting_date)
			if rule:
				if rule.commission_type == "Percentage":
					commission_amount = item.amount * (rule.value / 100.0)
				else:
					commission_amount = rule.value * item.qty

		# Priority 3: Fallback to Agent's default commission rate
		if not commission_amount and agent_doc.commission_rate > 0:
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
		frappe.db.commit()
		frappe.logger().info(f"Marketing fees accrued for Sales Agent: {sales_agent} on Invoice {doc.name}")


def _get_agent_commission_rule(agent, item_code, item_group, date):
	"""Find matching Sales Agent Commission Rule with 4-tier priority."""
	# Priority 1: Agent + Item
	rules = frappe.get_all("Sales Agent Commission Rule",
		filters={"sales_agent": agent, "item": item_code, "valid_from": ["<=", date]},
		fields=["name", "commission_type", "value", "valid_to"])
	valid_rule = next((r for r in rules if not r.valid_to or getdate(r.valid_to) >= getdate(date)), None)
	if valid_rule:
		return valid_rule

	# Priority 2: Agent + Item Group
	rules = frappe.get_all("Sales Agent Commission Rule",
		filters={"sales_agent": agent, "item_group": item_group, "valid_from": ["<=", date]},
		fields=["name", "commission_type", "value", "valid_to"])
	valid_rule = next((r for r in rules if not r.valid_to or getdate(r.valid_to) >= getdate(date)), None)
	if valid_rule:
		return valid_rule

	# Priority 3: Global + Item
	rules = frappe.get_all("Sales Agent Commission Rule",
		filters={"item": item_code, "valid_from": ["<=", date]},
		fields=["name", "commission_type", "value", "valid_to", "sales_agent"])
	valid_rule = next((r for r in rules if (not r.sales_agent) and (not r.valid_to or getdate(r.valid_to) >= getdate(date))), None)
	if valid_rule:
		return valid_rule

	# Priority 4: Global + Item Group
	rules = frappe.get_all("Sales Agent Commission Rule",
		filters={"item_group": item_group, "valid_from": ["<=", date]},
		fields=["name", "commission_type", "value", "valid_to", "sales_agent"])
	valid_rule = next((r for r in rules if (not r.sales_agent) and (not r.valid_to or getdate(r.valid_to) >= getdate(date))), None)
	if valid_rule:
		return valid_rule

	return None


def on_payment_entry_submit(doc, method):
	"""
	When a Payment Entry is submitted, check if any linked Sales/Purchase Invoices
	are now fully paid and trigger commission accrual, referral status update,
	or payout request completion.
	"""
	if doc.payment_type == "Receive":
		for ref in doc.references:
			if ref.reference_doctype == "Sales Invoice":
				invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
				if invoice.status == "Paid" or invoice.outstanding_amount <= 0:
					invoice.status = "Paid"
					on_invoice_paid(invoice, "on_payment_submit")

					from koraflow_core.koraflow_core.doctype.patient_referral.patient_referral import update_referral_on_invoice_paid
					update_referral_on_invoice_paid(invoice, "on_payment_submit")

	elif doc.payment_type == "Pay":
		# Check if a Purchase Invoice linked to a Payout Request was paid
		for ref in doc.references:
			if ref.reference_doctype == "Purchase Invoice":
				pi = frappe.get_doc("Purchase Invoice", ref.reference_name)
				if pi.outstanding_amount <= 0:
					_mark_payout_request_paid(pi.name)


def _mark_payout_request_paid(purchase_invoice_name):
	"""
	When a Purchase Invoice (payout) is paid, update the Payout Request
	and mark accruals as Paid (FIFO) up to the paid amount.
	"""
	payout_name = frappe.db.get_value(
		"Sales Agent Payout Request",
		{"generated_invoice": purchase_invoice_name, "docstatus": 1},
		"name"
	)
	if not payout_name:
		return

	payout = frappe.get_doc("Sales Agent Payout Request", payout_name)
	payout.db_set("status", "Paid")

	# Now check total paid out for this agent and mark accruals accordingly
	# Total paid = sum of all Paid payout requests
	paid_payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": payout.sales_agent, "status": "Paid", "docstatus": 1},
		fields=["amount"]
	)
	total_paid = sum(p.amount or 0 for p in paid_payouts)

	# Mark accruals as Paid (FIFO by creation) up to total_paid amount
	accruals = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": payout.sales_agent, "status": ["in", ["Accrued", "Requested"]]},
		fields=["name", "accrued_amount"],
		order_by="creation asc"
	)

	remaining = total_paid
	updated = 0
	for acc in accruals:
		if remaining <= 0:
			break
		frappe.db.set_value("Sales Agent Accrual", acc.name, "status", "Paid")
		remaining -= (acc.accrued_amount or 0)
		updated += 1

	if updated:
		frappe.db.commit()
		frappe.logger().info(
			f"Payout {payout_name} marked as Paid. {updated} accruals updated."
		)

