# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Healthcare Dispensing Automation Hooks
Implements automated workflow from prescription to dispense
"""

import frappe
from frappe import _
from frappe.utils import nowdate


def handle_prescription_approval(doc, method=None):
	"""
	On Prescription Approval:
	- Generate Quotation automatically
	"""
	if doc.doctype == "GLP-1 Patient Prescription" and doc.status == "Doctor Approved":
		# Also call existing workflow handler
		from koraflow_core.workflows.glp1_dispensing_workflow import handle_doctor_prescription_approval
		handle_doctor_prescription_approval(doc, method)
		# Create quotation
		create_quotation_from_prescription(doc)


def create_quotation_from_prescription(prescription):
	"""Auto-generate Quotation from approved prescription"""
	
	try:
		# Get medication item
		medication = frappe.db.get_value("GLP-1 Patient Prescription", prescription.name, "medication")
		if not medication:
			frappe.log_error("No medication found in prescription", "Prescription Approval")
			return
		
		# Get item from medication
		item_code = frappe.db.get_value(
			"Medication Linked Item",
			{"parent": medication},
			"item"
		)
		
		if not item_code:
			frappe.log_error(f"No item found for medication {medication}", "Prescription Approval")
			return
		
		# Get patient's customer
		patient = prescription.patient
		customer = frappe.db.get_value("Patient", patient, "customer")
		
		if not customer:
			frappe.log_error(f"No customer found for patient {patient}", "Prescription Approval")
			return
		
		# Get item price
		price_list = frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name") or "Standard Selling"
		item_price = frappe.db.get_value(
			"Item Price",
			{"item_code": item_code, "price_list": price_list},
			"price_list_rate"
		) or 0
		
		# Create quotation
		quotation = frappe.get_doc({
			"doctype": "Quotation",
			"party_type": "Customer",
			"party_name": customer,
			"quotation_to": "Customer",
			"items": [{
				"item_code": item_code,
				"qty": prescription.quantity,
				"rate": item_price,
				"uom": frappe.db.get_value("Item", item_code, "stock_uom")
			}],
			"custom_prescription": prescription.name,
			"valid_till": frappe.utils.add_days(nowdate(), 30)
		})
		
		quotation.flags.from_prescription = True
		quotation.insert(ignore_permissions=True)
		quotation.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Link quotation to prescription
		frappe.db.set_value("GLP-1 Patient Prescription", prescription.name, "quotation", quotation.name)
		
		frappe.msgprint(_("Quotation {0} created automatically").format(quotation.name))
		return quotation.name
		
	except Exception as e:
		frappe.log_error(f"Error creating quotation from prescription: {str(e)}", "Prescription Approval")


def handle_quotation_acceptance(doc, method=None):
	"""
	On Quote Acceptance:
	- Auto-create Sales Order
	- Auto-create Delivery Note
	- Auto-create Sales Invoice
	"""
	if doc.doctype == "Quotation" and doc.status == "Ordered":
		# Also call existing workflow handler
		from koraflow_core.workflows.glp1_dispensing_workflow import handle_quotation_accepted
		handle_quotation_accepted(doc, method)
		# Create sales chain
		create_sales_chain_from_quotation(doc)


def create_sales_chain_from_quotation(quotation):
	"""Auto-create Sales Order, Delivery Note, and Sales Invoice"""
	
	try:
		from erpnext.selling.doctype.quotation.quotation import make_sales_order
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
		
		# Create Sales Order
		sales_order = make_sales_order(quotation.name)
		sales_order.flags.from_quotation = True
		sales_order.insert(ignore_permissions=True)
		sales_order.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Create Delivery Note
		delivery_note = make_delivery_note(sales_order.name)
		delivery_note.flags.from_sales_order = True
		delivery_note.insert(ignore_permissions=True)
		delivery_note.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Create Sales Invoice
		sales_invoice = make_sales_invoice(sales_order.name)
		sales_invoice.flags.from_sales_order = True
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Trigger dispense task creation
		handle_invoice_submission(sales_invoice, None)
		
		frappe.msgprint(_("Sales chain created: {0} → {1} → {2}").format(
			sales_order.name, delivery_note.name, sales_invoice.name
		))
		
	except Exception as e:
		frappe.log_error(f"Error creating sales chain: {str(e)}", "Quotation Acceptance")


def handle_invoice_submission(doc, method=None):
	"""
	On Invoice Submission:
	- Create Dispense Task
	- Allocate stock logically to Virtual Hub
	- Queue pharmacist approval
	"""
	if doc.doctype == "Sales Invoice" and doc.docstatus == 1:
		create_dispense_task_from_invoice(doc)


def create_dispense_task_from_invoice(invoice):
	"""Create dispense task and allocation from invoice"""
	
	try:
		# Get prescription from quotation
		quotation = frappe.db.get_value("Sales Invoice", invoice.name, "quotation")
		if not quotation:
			return
		
		prescription = frappe.db.get_value("Quotation", quotation, "custom_prescription")
		if not prescription:
			return
		
		prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
		
		# Determine virtual hub (can be based on patient location or default)
		virtual_hub = "VIRTUAL-HUB-DEL-MAS"  # Default, can be customized
		
		# Create allocation
		if frappe.db.exists("DocType", "GLP-1 Dispense Allocation"):
			allocation = frappe.get_doc({
				"doctype": "GLP-1 Dispense Allocation",
				"prescription": prescription,
				"patient": prescription_doc.patient,
				"allocated_quantity": prescription_doc.quantity,
				"virtual_warehouse": virtual_hub,
				"status": "Reserved"
			})
			allocation.insert(ignore_permissions=True)
			allocation.submit(ignore_permissions=True)
			frappe.db.commit()
		
		# Create dispense task
		if frappe.db.exists("DocType", "GLP-1 Pharmacy Dispense Task"):
			dispense_task = frappe.get_doc({
				"doctype": "GLP-1 Pharmacy Dispense Task",
				"patient": prescription_doc.patient,
				"prescription": prescription,
				"allocation": allocation.name if frappe.db.exists("DocType", "GLP-1 Dispense Allocation") else None,
				"invoice": invoice.name,
				"status": "Pending"
			})
			dispense_task.insert(ignore_permissions=True)
			frappe.db.commit()
		
		frappe.msgprint(_("Dispense task created for invoice {0}").format(invoice.name))
		
	except Exception as e:
		frappe.log_error(f"Error creating dispense task: {str(e)}", "Invoice Submission")


def handle_pharmacist_approval(doc, method=None):
	"""
	On Pharmacist Approval (via GLP-1 Dispense Confirmation or Stock Entry):
	- Perform Stock Entry: PHARM-CENTRAL-COLD → Patient (Consumed)
	"""
	if doc.doctype == "GLP-1 Dispense Confirmation" and doc.docstatus == 1:
		create_stock_entry_from_dispense_confirmation(doc)
	elif doc.doctype == "Stock Entry" and doc.docstatus == 1:
		# Also call existing workflow handler
		from koraflow_core.workflows.glp1_dispensing_workflow import handle_pharmacist_dispense
		handle_pharmacist_dispense(doc, method)


def create_stock_entry_from_dispense_confirmation(confirmation):
	"""Create Stock Entry for dispense confirmation"""
	
	try:
		# Get prescription
		prescription = frappe.get_doc("GLP-1 Patient Prescription", confirmation.prescription)
		
		# Get medication item
		medication = prescription.medication
		item_code = frappe.db.get_value(
			"Medication Linked Item",
			{"parent": medication},
			"item"
		)
		
		if not item_code:
			frappe.log_error("No item found for medication", "Dispense Confirmation")
			return
		
		# Create Stock Entry
		stock_entry = frappe.get_doc({
			"doctype": "Stock Entry",
			"purpose": "Material Issue",
			"from_warehouse": "PHARM-CENTRAL-COLD",
			"to_warehouse": None,  # Consumed by patient
			"items": [{
				"item_code": item_code,
				"qty": prescription.quantity,
				"s_warehouse": "PHARM-CENTRAL-COLD",
				"batch_no": confirmation.batch,
				"basic_rate": frappe.db.get_value("Item Price", {"item_code": item_code}, "price_list_rate") or 0
			}],
			"custom_prescription": prescription.name,
			"custom_patient": prescription.patient,
			"reference_doctype": "GLP-1 Patient Prescription",
			"reference_name": prescription.name
		})
		
		stock_entry.flags.from_dispense_confirmation = True
		stock_entry.insert(ignore_permissions=True)
		stock_entry.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Link stock entry to confirmation
		frappe.db.set_value("GLP-1 Dispense Confirmation", confirmation.name, "stock_entry", stock_entry.name)
		
		frappe.msgprint(_("Stock Entry {0} created for dispense").format(stock_entry.name))
		
	except Exception as e:
		frappe.log_error(f"Error creating stock entry: {str(e)}", "Dispense Confirmation")
