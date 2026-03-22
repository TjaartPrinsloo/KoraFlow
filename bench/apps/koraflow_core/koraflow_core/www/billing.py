"""
Billing Page
"""
import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access this page"), frappe.PermissionError)
	
	roles = frappe.get_roles()
	if "Patient" not in roles and "System Manager" not in roles:
		frappe.throw(_("Access denied"), frappe.PermissionError)
	
	context.patient = None
	patient = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	
	# Debugging helper for Admin
	if not patient and "System Manager" in roles:
		# Try to find Lezel or any patient
		patient = frappe.db.get_value("Patient", {"email": "lezel@koraflow.com"}, "name")
		if not patient:
			patient = frappe.db.get_value("Patient", {}, "name")

	if not patient:
		frappe.local.flags.redirect_location = "/glp1-intake"
		raise frappe.Redirect
	
	context.patient = frappe.get_doc("Patient", patient)

	# Get Customer Link
	customer = frappe.db.get_value("Patient", patient, "customer")
	
	context.invoices = []
	context.outstanding_amount = 0
	
	if customer:
		# Get Invoices
		context.invoices = frappe.get_all(
			"Sales Invoice",
			filters={"customer": customer, "docstatus": 1},
			fields=["name", "posting_date", "grand_total", "outstanding_amount", "status", "due_date", "currency"],
			order_by="posting_date desc"
		)
		
		# Calculate totals
		context.total_invoiced = 0
		for inv in context.invoices:
			context.outstanding_amount += inv.outstanding_amount
			context.total_invoiced += inv.grand_total

		# Get Pending Quotations - Only show SUBMITTED quotes (not drafts)
		# Draft quotes are for sales team to assign agents before submitting
		context.quotations = frappe.get_all(
			"Quotation",
			filters={
				"party_name": customer,
				"docstatus": 1,  # Only submitted quotations
				"status": ["in", ["Open", "Replied", "Partially Ordered"]]  # Exclude Draft 
			},
			fields=["name", "transaction_date", "grand_total", "status", "currency", "title"],
			order_by="transaction_date desc",
			ignore_permissions=True
		)

	# Check for POP attachments on each invoice
	for inv in context.invoices:
		if not inv.currency: inv.currency = "ZAR"
		pop_file = frappe.db.get_value(
			"File",
			{"attached_to_doctype": "Sales Invoice", "attached_to_name": inv.name, "attached_to_field": "pop_attachment"},
			["name", "file_name", "file_url"],
			as_dict=True
		)
		inv.has_pop = bool(pop_file)
		inv.pop_file_name = pop_file.file_name if pop_file else None

	for qt in context.quotations:
		if not qt.currency: qt.currency = "ZAR"
