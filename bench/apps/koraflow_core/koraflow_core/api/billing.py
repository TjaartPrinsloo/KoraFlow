
import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice


def _render_branded_doc(doctype, name, print_format_name):
	"""Render a branded Jinja print format template directly."""
	from jinja2 import Template

	pf = frappe.get_doc("Print Format", print_format_name)
	doc = frappe.get_doc(doctype, name)
	template = Template(pf.html)
	body = template.render(doc=doc, frappe=frappe)

	return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>@page {{ size: A4; margin: 0; }} body {{ margin: 0; }}</style>
</head><body>{body}</body></html>"""


def _serve_pdf_or_html(html, name):
	"""Try to serve as PDF, fall back to HTML with auto-print."""
	try:
		from frappe.utils.pdf import get_pdf
		pdf_content = get_pdf(html)
		frappe.local.response.filename = f"{name}.pdf"
		frappe.local.response.filecontent = pdf_content
		frappe.local.response.type = "download"
		frappe.local.response.content_type = "application/pdf"
		frappe.local.response.display_content_as = "inline"
	except Exception:
		frappe.local.response.filename = f"{name}.html"
		frappe.local.response.filecontent = html
		frappe.local.response.type = "download"
		frappe.local.response.content_type = "text/html"
		frappe.local.response.display_content_as = "inline"

@frappe.whitelist()
def accept_quotation(quotation_name):
	"""
	Accepts a quotation:
	1. Validates ownership (Patient -> Customer -> Quotation)
	2. Creates Sales Order from Quotation
	3. Submits Sales Order
	4. Creates Sales Invoice from Sales Order
	5. Submits Sales Invoice
	"""
	try:
		if frappe.session.user == "Guest":
			frappe.throw(_("Please log in to perform this action"), frappe.PermissionError)

		# 1. Validate Patient & Quotation Ownership
		# 1. Validate Patient & Quotation Ownership
		patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
		
		# Debug fallback for System Manager
		if not patient_name and "System Manager" in frappe.get_roles():
			patient_name = frappe.db.get_value("Patient", {"email": "lezel@koraflow.com"}, "name")
			if not patient_name:
				patient_name = frappe.db.get_value("Patient", {}, "name")

		if not patient_name:
			frappe.throw(_("Patient record not found for this user"), frappe.PermissionError)

		customer_name = frappe.db.get_value("Patient", patient_name, "customer")
		if not customer_name:
			frappe.throw(_("No customer account linked to this patient"), frappe.ValidationError)

		# Check if quotation exists and belongs to this customer
		quotation = frappe.get_doc("Quotation", quotation_name)
		if quotation.party_name != customer_name:
			frappe.throw(_("Access Denied: This quotation belongs to another customer"), frappe.PermissionError)

		if quotation.status != "Open":
			# If it's already accepted/ordered, just return success or info
			if quotation.status in ["Ordered", "Converted"]:
				return {"message": _("Quotation is already accepted"), "status": "Already Accepted"}
			frappe.throw(_("Quotation status is {0}, cannot accept.").format(quotation.status))

		# 2. Create Sales Order
		# Switch to Administrator to bypass all permission checks including get_mapped_doc
		original_user = frappe.session.user
		frappe.set_user("Administrator")
		frappe.flags.in_accept_quotation = True
		
		try:
			# make_sales_order returns a transient JS object (Sales Order doc), not saved yet
			sales_order = make_sales_order(quotation_name)
			
			# Set transaction_date to today to ensure all date validations pass
			today_date = getdate()
			sales_order.transaction_date = today_date
			sales_order.delivery_date = today_date  # Required field
			
			# CRITICAL: Clear payment schedule copied from old quotation
			# Old quotations may have due dates in the past which fail validation
			# "Due Date in Payment Terms table cannot be before Posting Date"
			sales_order.payment_terms_template = None
			sales_order.payment_schedule = []
			
			# Set default warehouse if missing (often needed for stock items)
			default_warehouse = frappe.db.get_single_value('Stock Settings', 'default_warehouse') 
			if not default_warehouse:
				# Fallback to first non-group warehouse
				default_warehouse = frappe.db.get_value('Warehouse', {'is_group': 0, 'company': sales_order.company}, 'name')
			
			if default_warehouse:
				for item in sales_order.items:
					if not item.warehouse:
						item.warehouse = default_warehouse

			sales_order.insert(ignore_permissions=True)
			sales_order.submit()
			
			frappe.db.commit() # Commit SO creation
	
			# 3. Create Sales Invoice
			# make_sales_invoice also returns a transient object
			sales_invoice = make_sales_invoice(sales_order.name)

			# Ensure Posting Date is today
			today_date = getdate()
			sales_invoice.posting_date = today_date
			
			# Set Due Date to 24 hours after Posting Date (Tomorrow)
			from frappe.utils import add_days, flt
			due_date = add_days(today_date, 1)
			sales_invoice.due_date = due_date
			
			# Disable any pre-calculated payment terms template that might cause conflict
			sales_invoice.payment_terms_template = None
			
			# Explicitly construct a valid Payment Schedule to prevent auto-fetching defaults
			# that might have conflicting dates.
			sales_invoice.payment_schedule = []
			sales_invoice.append("payment_schedule", {
				"due_date": due_date,
				"payment_amount": sales_invoice.grand_total,
				"invoice_portion": 100.0,
				"description": "Portion 1"
			})

			sales_invoice.insert(ignore_permissions=True)
			sales_invoice.submit()
	
			frappe.db.commit() # Commit SI creation
		except Exception:
			# Re-raise to be caught by outer handler
			raise
		finally:
			frappe.set_user(original_user) # Always restore user!
			frappe.flags.in_accept_quotation = False

		# Reload docs to get clean state if needed, or just return names
		return {
			"success": True,
			"message": _("Quotation accepted successfully. Invoice generated."),
			"sales_order": sales_order.name,
			"sales_invoice": sales_invoice.name
		}

	except Exception as e:
		import traceback
		traceback_str = traceback.format_exc()
		frappe.log_error(title="Quotation Acceptance Error", message=f"Error accepting quotation {quotation_name}: {traceback_str}")
		return {
			"success": False,
			"error": str(e) or "Unknown Error - Check Logs"
		}

@frappe.whitelist()
def reject_quotation(quotation_name):
	"""
	Rejects a quotation by setting status to 'Lost'.
	"""
	try:
		if frappe.session.user == "Guest":
			frappe.throw(_("Please log in to perform this action"), frappe.PermissionError)

		# 1. Validate Patient & Quotation Ownership
		# 1. Validate Patient & Quotation Ownership
		patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
		
		# Debug fallback for System Manager
		if not patient_name and "System Manager" in frappe.get_roles():
			patient_name = frappe.db.get_value("Patient", {"email": "lezel@koraflow.com"}, "name")
			if not patient_name:
				# Fallback to any patient if Lezel not found
				patient_name = frappe.db.get_value("Patient", {}, "name")

		if not patient_name:
			frappe.throw(_("Patient record not found for this user"), frappe.PermissionError)

		customer_name = frappe.db.get_value("Patient", patient_name, "customer")
		if not customer_name:
			frappe.throw(_("No customer account linked to this patient"), frappe.ValidationError)

		# Check if quotation exists and belongs to this customer
		quotation = frappe.get_doc("Quotation", quotation_name)
		if quotation.party_name != customer_name:
			frappe.throw(_("Access Denied: This quotation belongs to another customer"), frappe.PermissionError)

		if quotation.status != "Open":
			if quotation.status == "Lost":
				return {"message": _("Quotation is already rejected"), "status": "Already Rejected"}
			frappe.throw(_("Quotation status is {0}, cannot reject.").format(quotation.status))

		# 2. Reject Quotation (Set to Lost)
		# Use set_value to bypass "not allowed to change status after submit" validation if standard save fails
		frappe.db.set_value("Quotation", quotation_name, "status", "Lost")
		
		frappe.db.commit()

		return {
			"success": True,
			"message": _("Quotation rejected.")
		}

	except Exception as e:
		frappe.log_error(title="Quotation Rejection Error", message=f"Error rejecting quotation {quotation_name}: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def upload_pop(invoice_name):
	"""
	Upload Proof of Payment for a Sales Invoice.
	Validates patient ownership, then attaches the uploaded file to the invoice.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to perform this action"), frappe.PermissionError)

	# Validate ownership
	patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	if not patient_name and "System Manager" in frappe.get_roles():
		patient_name = frappe.db.get_value("Patient", {"email": "lezel@koraflow.com"}, "name")
		if not patient_name:
			patient_name = frappe.db.get_value("Patient", {}, "name")

	if not patient_name:
		frappe.throw(_("Patient record not found"), frappe.PermissionError)

	customer_name = frappe.db.get_value("Patient", patient_name, "customer")
	invoice_customer = frappe.db.get_value("Sales Invoice", invoice_name, "customer")

	if not invoice_customer or invoice_customer != customer_name:
		frappe.throw(_("Access Denied"), frappe.PermissionError)

	# Get the uploaded file from the request
	filedata = frappe.request.files.get("file")
	if not filedata:
		frappe.throw(_("No file uploaded"))

	# Remove any existing POP attachment for this invoice
	existing = frappe.db.get_value(
		"File",
		{"attached_to_doctype": "Sales Invoice", "attached_to_name": invoice_name, "attached_to_field": "pop_attachment"},
		"name"
	)
	if existing:
		frappe.delete_doc("File", existing, ignore_permissions=True)

	# Save the file and attach to the invoice
	from frappe.utils.file_manager import save_file
	file_doc = save_file(
		fname=filedata.filename,
		content=filedata.read(),
		dt="Sales Invoice",
		dn=invoice_name,
		folder="Home/Attachments",
		is_private=1
	)
	# Tag it so we can identify POP attachments specifically
	file_doc.attached_to_field = "pop_attachment"
	file_doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"success": True,
		"message": _("Proof of Payment uploaded successfully."),
		"file_name": file_doc.file_name
	}


@frappe.whitelist()
def download_quotation_pdf(quotation_name):
	"""
	Generates and returns the branded Quotation PDF.
	Verifies Patient ownership before serving.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to access this document"), frappe.PermissionError)

	# Validate ownership
	patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	if not patient_name and "System Manager" in frappe.get_roles():
		patient_name = frappe.db.get_value("Patient", {}, "name")

	if not patient_name:
		frappe.throw(_("Patient record not found"), frappe.PermissionError)

	customer_name = frappe.db.get_value("Patient", patient_name, "customer")
	quotation_customer = frappe.db.get_value("Quotation", quotation_name, "party_name")

	if not quotation_customer or quotation_customer != customer_name:
		frappe.throw(_("Access Denied"), frappe.PermissionError)

	# Generate branded PDF using Jinja print format
	html = _render_branded_doc("Quotation", quotation_name, "Slim 2 Well Quotation")
	_serve_pdf_or_html(html, quotation_name)

@frappe.whitelist()
def download_invoice_pdf(invoice_name):
	"""
	Generates and returns the branded Invoice PDF.
	Verifies Patient ownership before serving.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to access this document"), frappe.PermissionError)

	# Validate ownership
	patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	if not patient_name and "System Manager" in frappe.get_roles():
		patient_name = frappe.db.get_value("Patient", {}, "name")

	if not patient_name:
		frappe.throw(_("Patient record not found"), frappe.PermissionError)

	customer_name = frappe.db.get_value("Patient", patient_name, "customer")
	invoice_customer = frappe.db.get_value("Sales Invoice", invoice_name, "customer")

	if not invoice_customer or invoice_customer != customer_name:
		frappe.throw(_("Access Denied"), frappe.PermissionError)

	# Generate branded PDF using Jinja print format
	html = _render_branded_doc("Sales Invoice", invoice_name, "Slim 2 Well Invoice")
	_serve_pdf_or_html(html, invoice_name)

@frappe.whitelist()
def download_prescription_pdf(prescription_name):
	"""
	Generates and returns the Prescription PDF/HTML.
	Bypasses standard permission checks but verifies Patient ownership.
	"""
	try:
		if frappe.session.user == "Guest":
			frappe.throw(_("Please log in to access this document"), frappe.PermissionError)

		# 1. Validate Patient & Prescription Ownership
		patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
		
		# Debug fallback for System Manager
		if not patient_name and "System Manager" in frappe.get_roles():
			patient_name = frappe.db.get_value("Patient", {"email": "lezel@koraflow.com"}, "name")
			if not patient_name:
				patient_name = frappe.db.get_value("Patient", {}, "name")

		if not patient_name:
			frappe.throw(_("Patient record not found"), frappe.PermissionError)

		# Check if prescription exists and belongs to this patient
		prescription_patient = frappe.db.get_value("GLP-1 Patient Prescription", prescription_name, "patient")
		
		if not prescription_patient or prescription_patient != patient_name:
			frappe.throw(_("Access Denied: Document not found or unauthorized"), frappe.PermissionError)

		# 2. Generate PDF/HTML using system permissions
		from frappe.utils.pdf import get_pdf
		
		prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
		
		frappe.flags.ignore_print_permissions = True
		
		try:
			# Get HTML first
			html = frappe.get_print(
				doctype="GLP-1 Patient Prescription",
				name=prescription_name,
				print_format="Standard",
				doc=prescription_doc,
				as_pdf=False # Get HTML
			)
			
			# Generate PDF from HTML
			try:
				pdf_content = get_pdf(html)
				
				frappe.local.response.filename = f"{prescription_name}.pdf"
				frappe.local.response.filecontent = pdf_content
				frappe.local.response.type = "download"
				frappe.local.response.content_type = "application/pdf"
				frappe.local.response.display_content_as = "inline"
				
			except Exception:
				# Fallback to HTML if PDF generation failure
				fallback_html = f"""
				<html class="pdf-fallback">
					<head>
						<style>
							@media print {{ @page {{ margin: 0; }} }}
							.print-view-header, .navbar, .app-header, .action-banner {{ display: none !important; }}
						</style>
						<script>
							window.onload = function() {{
								setTimeout(function() {{
									window.print();
								}}, 500);
							}};
						</script>
					</head>
					<body>
						{html}
					</body>
				</html>
				"""
				frappe.local.response.filename = f"{prescription_name}.html"
				frappe.local.response.filecontent = fallback_html
				frappe.local.response.type = "download"
				frappe.local.response.content_type = "text/html"
				frappe.local.response.display_content_as = "inline"

		finally:
			# Always reset the flag
			frappe.flags.ignore_print_permissions = False

	except Exception as e:
		print(f"Document generation error for {prescription_name}: {str(e)}")
		try:
			frappe.flags.ignore_print_permissions = True
			html = frappe.get_print(doctype="GLP-1 Patient Prescription", name=prescription_name, print_format="Standard")
			fallback_html = f"<html class='pdf-fallback'><head><script>window.onload = function() {{ window.print(); }};</script></head><body>{html}</body></html>"
			frappe.local.response.filename = f"{prescription_name}.html"
			frappe.local.response.filecontent = fallback_html
			frappe.local.response.type = "download"
			frappe.local.response.content_type = "text/html"
			frappe.local.response.display_content_as = "inline"
		except Exception as fallback_error:
			frappe.flags.ignore_print_permissions = False
			frappe.throw(_("Unable to generate document request."))
		finally:
			frappe.flags.ignore_print_permissions = False

