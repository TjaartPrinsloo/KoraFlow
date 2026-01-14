# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Audit Replay Report
Reconstructs the complete chain from prescription to dispense
"""

import frappe
from frappe import _


def execute(filters=None):
	"""Generate audit replay report"""
	
	columns = [
		{"label": _("Step"), "fieldname": "step", "fieldtype": "Data", "width": 100},
		{"label": _("Document Type"), "fieldname": "doctype", "fieldtype": "Link", "options": "DocType", "width": 150},
		{"label": _("Document Name"), "fieldname": "docname", "fieldtype": "Dynamic Link", "options": "doctype", "width": 200},
		{"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},
		{"label": _("Doctor"), "fieldname": "doctor", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 150},
		{"label": _("Pharmacist"), "fieldname": "pharmacist", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Sales Partner"), "fieldname": "sales_partner", "fieldtype": "Link", "options": "Sales Partner", "width": 150},
		{"label": _("Commission"), "fieldname": "commission", "fieldtype": "Currency", "width": 100},
		{"label": _("Batch"), "fieldname": "batch", "fieldtype": "Link", "options": "Batch", "width": 120},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Datetime", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100}
	]
	
	data = []
	
	# Get filters
	prescription = filters.get("prescription") if filters else None
	patient = filters.get("patient") if filters else None
	batch = filters.get("batch") if filters else None
	
	if not prescription and not patient and not batch:
		return columns, data
	
	# Start from prescription or find prescription
	if prescription:
		prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
		patient = prescription_doc.patient
	elif patient:
		# Get latest prescription
		prescription = frappe.db.get_value(
			"GLP-1 Patient Prescription",
			{"patient": patient},
			"name",
			order_by="creation desc"
		)
		if prescription:
			prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
		else:
			return columns, data
	else:
		# Find prescription from batch
		dispense_confirmation = frappe.db.get_value(
			"GLP-1 Dispense Confirmation",
			{"batch": batch},
			"prescription"
		)
		if dispense_confirmation:
			prescription = dispense_confirmation
			prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
			patient = prescription_doc.patient
		else:
			return columns, data
	
	# Step 1: Prescription
	data.append({
		"step": "1. Prescription",
		"doctype": "GLP-1 Patient Prescription",
		"docname": prescription_doc.name,
		"patient": prescription_doc.patient,
		"doctor": prescription_doc.doctor,
		"date": prescription_doc.creation,
		"status": prescription_doc.status
	})
	
	# Step 2: Quotation
	quotation = frappe.db.get_value("Quotation", {"custom_prescription": prescription}, "name")
	if quotation:
		quotation_doc = frappe.get_doc("Quotation", quotation)
		data.append({
			"step": "2. Quotation",
			"doctype": "Quotation",
			"docname": quotation,
			"patient": patient,
			"date": quotation_doc.creation,
			"status": quotation_doc.status
		})
		
		# Step 3: Sales Order
		sales_order = frappe.db.get_value("Sales Order", {"quotation": quotation}, "name")
		if sales_order:
			sales_order_doc = frappe.get_doc("Sales Order", sales_order)
			data.append({
				"step": "3. Sales Order",
				"doctype": "Sales Order",
				"docname": sales_order,
				"patient": patient,
				"sales_partner": sales_order_doc.sales_partner if hasattr(sales_order_doc, 'sales_partner') else None,
				"date": sales_order_doc.creation,
				"status": sales_order_doc.status
			})
			
			# Step 4: Delivery Note
			delivery_note = frappe.db.get_value("Delivery Note", {"sales_order": sales_order}, "name")
			if delivery_note:
				delivery_note_doc = frappe.get_doc("Delivery Note", delivery_note)
				data.append({
					"step": "4. Delivery Note",
					"doctype": "Delivery Note",
					"docname": delivery_note,
					"patient": patient,
					"date": delivery_note_doc.creation,
					"status": delivery_note_doc.status
				})
			
			# Step 5: Sales Invoice
			sales_invoice = frappe.db.get_value("Sales Invoice", {"sales_order": sales_order}, "name")
			if sales_invoice:
				sales_invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice)
				commission = frappe.db.get_value(
					"Sales Partner Commission",
					{"sales_invoice": sales_invoice},
					"commission_amount"
				) or 0
				
				data.append({
					"step": "5. Sales Invoice",
					"doctype": "Sales Invoice",
					"docname": sales_invoice,
					"patient": patient,
					"sales_partner": sales_invoice_doc.sales_partner if hasattr(sales_invoice_doc, 'sales_partner') else None,
					"commission": commission,
					"date": sales_invoice_doc.creation,
					"status": sales_invoice_doc.status
				})
				
				# Step 6: Dispense Task
				dispense_task = frappe.db.get_value("GLP-1 Pharmacy Dispense Task", {"invoice": sales_invoice}, "name")
				if dispense_task:
					dispense_task_doc = frappe.get_doc("GLP-1 Pharmacy Dispense Task", dispense_task)
					data.append({
						"step": "6. Dispense Task",
						"doctype": "GLP-1 Pharmacy Dispense Task",
						"docname": dispense_task,
						"patient": patient,
						"date": dispense_task_doc.creation,
						"status": dispense_task_doc.status
					})
	
	# Step 7: Stock Entry
	stock_entry = frappe.db.get_value("Stock Entry", {"custom_prescription": prescription}, "name")
	if stock_entry:
		stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry)
		batch_no = stock_entry_doc.items[0].batch_no if stock_entry_doc.items else None
		warehouse = stock_entry_doc.items[0].s_warehouse if stock_entry_doc.items else None
		
		data.append({
			"step": "7. Stock Entry",
			"doctype": "Stock Entry",
			"docname": stock_entry,
			"patient": patient,
			"batch": batch_no,
			"warehouse": warehouse,
			"date": stock_entry_doc.creation,
			"status": "Submitted" if stock_entry_doc.docstatus == 1 else "Draft"
		})
	
	# Step 8: Dispense Confirmation
	dispense_confirmation = frappe.db.get_value("GLP-1 Dispense Confirmation", {"prescription": prescription}, "name")
	if dispense_confirmation:
		dispense_confirmation_doc = frappe.get_doc("GLP-1 Dispense Confirmation", dispense_confirmation)
		data.append({
			"step": "8. Dispense Confirmation",
			"doctype": "GLP-1 Dispense Confirmation",
			"docname": dispense_confirmation,
			"patient": patient,
			"pharmacist": dispense_confirmation_doc.pharmacist,
			"batch": dispense_confirmation_doc.batch,
			"date": dispense_confirmation_doc.creation,
			"status": "Submitted" if dispense_confirmation_doc.docstatus == 1 else "Draft"
		})
	
	# Step 9: Audit Logs
	audit_logs = frappe.get_all(
		"GLP-1 Compliance Audit Log",
		filters={"reference_name": prescription},
		fields=["name", "event_type", "actor", "timestamp"]
	)
	
	for log in audit_logs:
		data.append({
			"step": f"9. Audit: {log.event_type}",
			"doctype": "GLP-1 Compliance Audit Log",
			"docname": log.name,
			"patient": patient,
			"date": log.timestamp
		})
	
	return columns, data
