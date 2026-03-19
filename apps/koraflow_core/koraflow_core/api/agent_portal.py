import frappe
from frappe import _
from frappe.utils import flt, today, getdate


@frappe.whitelist()
def request_payout(amount):
	"""
	Creates a Sales Agent Payout Request, marks accruals as Requested,
	and submits to generate a Purchase Invoice.
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in to request payout."))

	sales_agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not sales_agent:
		frappe.throw(_("No Sales Agent account found for this user."))

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Invalid amount requested."))

	# Check available balance = unpaid commissions minus pending payout requests
	accruals = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": sales_agent, "status": ["in", ["Accrued", "Requested"]]},
		fields=["name", "accrued_amount"],
		order_by="creation asc"
	)
	total_unpaid = sum(flt(d.accrued_amount) for d in accruals)

	pending_payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": sales_agent, "status": ["in", ["Pending", "Approved"]], "docstatus": 1},
		fields=["amount"]
	)
	total_pending_payouts = sum(flt(p.amount) for p in pending_payouts)
	available_balance = max(total_unpaid - total_pending_payouts, 0)

	if amount > available_balance:
		frappe.throw(_(
			"Requested amount (R {0:,.2f}) exceeds available balance (R {1:,.2f})."
		).format(amount, available_balance))

	# Create Payout Request
	pr = frappe.get_doc({
		"doctype": "Sales Agent Payout Request",
		"sales_agent": sales_agent,
		"request_date": today(),
		"amount": amount,
		"status": "Pending"
	})
	pr.insert(ignore_permissions=True)

	# Submit — triggers on_submit which creates the Purchase Invoice
	pr.submit()
	frappe.db.commit()

	return {"message": "Payout request submitted successfully", "name": pr.name}


@frappe.whitelist()
def update_banking_details(bank_name, account_holder, account_number, branch_code, account_type):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in."))

	sales_agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not sales_agent:
		frappe.throw(_("No Sales Agent account found."))

	details = f"{bank_name}\n{account_holder}\n{account_number}\n{branch_code}\n{account_type}"

	frappe.db.set_value("Sales Agent", sales_agent, "bank_details", details)
	frappe.db.commit()

	return {"message": "Banking details updated"}


@frappe.whitelist()
def get_dashboard_data():
	"""Returns data for the dashboard."""
	user = frappe.session.user
	if user == "Guest":
		return {}

	sales_agent = frappe.db.get_value("Sales Agent", {"user": user}, "name")
	if not sales_agent:
		return {"error": "Not a Sales Agent"}

	agent_doc = frappe.get_doc("Sales Agent", sales_agent)

	# Referrals
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": sales_agent},
		fields=["name", "patient_first_name", "patient_last_name", "current_journey_status", "creation", "status"],
		order_by="creation desc"
	)

	# Commissions/Accruals
	accruals = frappe.get_all(
		"Sales Agent Accrual",
		filters={"sales_agent": sales_agent},
		fields=["creation", "accrued_amount", "status", "invoice_reference", "patient"],
		order_by="creation desc"
	)

	# Payout Requests
	payouts = frappe.get_all(
		"Sales Agent Payout Request",
		filters={"sales_agent": sales_agent},
		fields=["name", "amount", "status", "request_date", "generated_invoice"],
		order_by="request_date desc"
	)

	total_earned = sum(flt(c.accrued_amount) for c in accruals)
	total_paid = sum(flt(c.accrued_amount) for c in accruals if c.status == "Paid")
	total_pending = sum(flt(c.accrued_amount) for c in accruals if c.status == "Requested")
	available = sum(flt(c.accrued_amount) for c in accruals if c.status == "Accrued")

	return {
		"agent": {
			"name": f"{agent_doc.first_name} {agent_doc.last_name}",
			"id": agent_doc.name,
			"bank_details_configured": bool(agent_doc.bank_details)
		},
		"referrals": referrals,
		"recent_payouts": payouts[:5],
		"totals": {
			"earned": total_earned,
			"paid": total_paid,
			"pending": total_pending,
			"available": available
		}
	}
