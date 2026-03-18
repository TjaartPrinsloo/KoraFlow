# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Dispensing Workflow
State machine workflow with automation boundaries and human gates
"""

import frappe
from frappe import _
from frappe.utils import now


def handle_intake_submission(doc, method):
	"""Step 1: Patient submits intake form - Auto-assign nurse"""
	if doc.doctype == "GLP-1 Intake Submission":
		# Create intake review
		review = frappe.get_doc({
			"doctype": "GLP-1 Intake Review",
			"intake_submission": doc.name,
			"status": "Pending"
		})
		review.insert(ignore_permissions=True)
		frappe.db.commit()


def handle_nurse_review_approval(doc, method):
	"""Step 2-3: Nurse reviews and approves - Human Gate #1"""
	if doc.doctype == "GLP-1 Intake Review" and doc.status == "Approved":
		# Nurse can suggest prescription (draft only)
		# This is handled in the DocType on_update
		pass


def handle_doctor_prescription_approval(doc, method):
	"""Step 4-6: Doctor approves prescription - LEGAL GATE"""
	if doc.doctype == "GLP-1 Patient Prescription" and doc.status == "Doctor Approved":
		# Create audit log
		from koraflow_core.utils.glp1_compliance import create_audit_log
		create_audit_log(
			event_type="Prescription",
			reference_doctype="GLP-1 Patient Prescription",
			reference_name=doc.name,
			patient=doc.patient,
			actor=frappe.session.user,
			details={"medication": doc.medication, "dosage": doc.dosage}
		)
		
		# Auto-generate quote (Step 7)
		create_quotation_from_prescription(doc)


def create_quotation_from_prescription(prescription):
	"""Step 7: Auto-generate quotation"""
	try:
		# Get medication item
		medication = frappe.get_doc("Medication", prescription.medication)
		medication_item = medication.item if hasattr(medication, 'item') else None
		
		if not medication_item:
			frappe.log_error(title="GLP-1 Workflow", message=f"No item found for medication {prescription.medication}")
			return
		
		# Create quotation
		quotation = frappe.get_doc({
			"doctype": "Quotation",
			"party_type": "Customer",
			"party": frappe.db.get_value("Patient", prescription.patient, "customer"),
			"items": [{
				"item_code": medication_item,
				"qty": prescription.quantity,
				"rate": frappe.db.get_value("Item", medication_item, "standard_rate") or 0
			}]
		})
		quotation.flags.from_medication_request = True
		quotation.insert(ignore_permissions=True)
		quotation.flags.ignore_permissions = True
		quotation.submit()
		frappe.db.commit()
		
		return quotation.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Workflow", message=f"Error creating quotation: {str(e)}")


def handle_quotation_accepted(doc, method):
	"""Step 8: Patient accepts quote - HUMAN GATE #3"""
	if doc.doctype == "Quotation" and doc.status == "Ordered":
		# Auto-create sales chain (Step 9-10)
		create_sales_chain_from_quotation(doc)


def create_sales_chain_from_quotation(quotation):
	"""Step 9-10: Auto-create Sales Order, Delivery Note, Invoice"""
	try:
		frappe.flags.in_accept_quotation = True
		from erpnext.selling.doctype.quotation.quotation import make_sales_order
		
		# Create Sales Order
		sales_order = make_sales_order(quotation.name)
		sales_order.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 1)

		# Set Warehouse and carry prescription link
		pharm_warehouse = frappe.db.get_value("Pharmacy Warehouse", {"warehouse_name": "PHARM-CENTRAL-COLD"}, "erpnext_warehouse")
		prescription_name = getattr(quotation, 'custom_prescription', None)

		for item in sales_order.items:
			if not item.warehouse and pharm_warehouse:
				item.warehouse = pharm_warehouse
			# Carry prescription link from quotation items
			if prescription_name and hasattr(item, 'custom_prescription'):
				item.custom_prescription = prescription_name

		# Link prescription at SO level too
		if prescription_name and hasattr(sales_order, 'custom_prescription'):
			sales_order.custom_prescription = prescription_name

		if hasattr(quotation, 'custom_delivery_notes'):
			sales_order.custom_delivery_notes = quotation.custom_delivery_notes

		sales_order.flags.from_medication_request = True
		sales_order.insert(ignore_permissions=True)
		sales_order.flags.ignore_permissions = True
		sales_order.submit()
		frappe.db.commit()
		
		# Create Delivery Note
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		delivery_note = make_delivery_note(sales_order.name)
		delivery_note.flags.from_medication_request = True
		if hasattr(sales_order, 'custom_delivery_notes'):
			delivery_note.custom_delivery_notes = sales_order.custom_delivery_notes
		delivery_note.insert(ignore_permissions=True)
		# delivery_note.flags.ignore_permissions = True
		# delivery_note.submit()
		frappe.db.commit()
		
		# Create Sales Invoice
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
		sales_invoice = make_sales_invoice(sales_order.name)
		sales_invoice.flags.from_medication_request = True
		if hasattr(sales_order, 'custom_delivery_notes'):
			sales_invoice.custom_delivery_notes = sales_order.custom_delivery_notes
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.flags.ignore_permissions = True
		sales_invoice.submit()
		frappe.db.commit()
		
		# Create dispense allocation (Step 11)
		create_dispense_allocation_from_invoice(sales_invoice)
		
		return sales_invoice.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Workflow", message=f"Error creating sales chain: {str(e)}")
	finally:
		frappe.flags.in_accept_quotation = False


def create_dispense_allocation_from_invoice(invoice):
	"""Step 11: Auto-create virtual allocation"""
	try:
		# Get prescription from invoice items
		# This is a simplified version - adjust based on your linking structure
		prescription_name = None
		patient = invoice.party_name if hasattr(invoice, 'party_name') else None
		
		if not patient:
			# Try to get from customer
			customer = invoice.customer
			patient = frappe.db.get_value("Patient", {"customer": customer}, "name")
		
		if patient:
			# Find latest approved prescription for this patient
			prescription = frappe.db.get_value(
				"GLP-1 Patient Prescription",
				{"patient": patient, "status": "Doctor Approved"},
				"name",
				order_by="creation desc"
			)
			
			if prescription:
				prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
				
				# Create allocation
				allocation = frappe.get_doc({
					"doctype": "GLP-1 Dispense Allocation",
					"prescription": prescription,
					"patient": patient,
					"allocated_quantity": prescription_doc.quantity,
					"status": "Reserved"
				})
				allocation.insert(ignore_permissions=True)
				frappe.db.commit()
				
				# Create dispense task (Step 12)
				create_dispense_task(allocation, invoice)
				
				return allocation.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Workflow", message=f"Error creating allocation: {str(e)}")


def create_dispense_task(allocation, invoice):
	"""Step 12: Create pharmacy dispense task"""
	try:
		task = frappe.get_doc({
			"doctype": "GLP-1 Pharmacy Dispense Task",
			"patient": allocation.patient,
			"prescription": allocation.prescription,
			"allocation": allocation.name,
			"invoice": invoice.name,
			"status": "Pending"
		})
		task.insert(ignore_permissions=True)
		frappe.db.commit()
		return task.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Workflow", message=f"Error creating dispense task: {str(e)}")


def handle_pharmacist_dispense(doc, method):
	"""Step 13: Pharmacist dispenses - LEGAL GATE #4 - ONLY REAL STOCK MOVE"""
	if doc.doctype == "Stock Entry" and doc.purpose == "Material Issue":
		# Verify this is from PHARM-CENTRAL-COLD
		pharm_warehouse = frappe.db.get_value(
			"Pharmacy Warehouse",
			{"warehouse_name": "PHARM-CENTRAL-COLD"},
			"erpnext_warehouse"
		)
		
		if pharm_warehouse:
			for item in doc.items:
				if item.s_warehouse == pharm_warehouse:
					# This is a GLP-1 dispense
					# Create dispense confirmation (Step 14)
					create_dispense_confirmation(doc, item)
					break


def create_dispense_confirmation(stock_entry, item):
	"""Step 14: Create dispense confirmation"""
	try:
		# Get patient from custom field or linked document
		patient = None
		if hasattr(stock_entry, 'custom_patient'):
			patient = stock_entry.custom_patient
		
		if not patient:
			# Try to find from allocation or task
			allocation = frappe.db.get_value(
				"GLP-1 Dispense Allocation",
				{"status": "Reserved"},
				["patient", "prescription"],
				as_dict=True,
				order_by="creation desc",
				limit=1
			)
			if allocation:
				patient = allocation.patient
				prescription = allocation.prescription
		
		if patient:
			confirmation = frappe.get_doc({
				"doctype": "GLP-1 Dispense Confirmation",
				"prescription": prescription if 'prescription' in locals() else None,
				"patient": patient,
				"stock_entry": stock_entry.name,
				"batch": item.batch_no,
				"pharmacist": frappe.session.user,
				"patient_acknowledgment": 0  # To be set by pharmacist
			})
			confirmation.insert(ignore_permissions=True)
			frappe.db.commit()
			return confirmation.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Workflow", message=f"Error creating dispense confirmation: {str(e)}")
