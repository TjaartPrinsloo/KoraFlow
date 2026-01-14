# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Pharmacist API
APIs for pharmacist dashboard and dispense operations
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_dispense_queue():
	"""Get pending dispense tasks for pharmacist"""
	tasks = frappe.get_all(
		"GLP-1 Pharmacy Dispense Task",
		filters={"status": ["in", ["Pending", "In Progress"]]},
		fields=["name", "patient", "prescription", "allocation", "status"],
		order_by="creation asc"
	)
	
	# Enrich with patient names and batch availability
	for task in tasks:
		# Get patient name
		if task.patient:
			task.patient_name = frappe.db.get_value("Patient", task.patient, "patient_name")
		
		# Get batch availability
		task_doc = frappe.get_doc("GLP-1 Pharmacy Dispense Task", task.name)
		if task_doc.batch_availability:
			task.batch_availability = [
				{
					"batch": b.batch,
					"expiry_date": str(b.expiry_date) if b.expiry_date else None,
					"available_quantity": b.available_quantity
				}
				for b in task_doc.batch_availability
			]
		
		# Get allocated quantity
		if task.allocation:
			task.allocated_quantity = frappe.db.get_value(
				"GLP-1 Dispense Allocation",
				task.allocation,
				"allocated_quantity"
			)
	
	return {"tasks": tasks}


@frappe.whitelist()
def create_dispense(task, batch, quantity, patient_acknowledged, counseling_notes=None):
	"""Create dispense from task"""
	try:
		task_doc = frappe.get_doc("GLP-1 Pharmacy Dispense Task", task)
		
		# Validate cold chain
		from koraflow_core.utils.glp1_compliance import check_cold_chain_compliance
		cold_chain = check_cold_chain_compliance(batch)
		if not cold_chain["compliant"]:
			return {"success": False, "message": cold_chain["message"]}
		
		# Get PHARM-CENTRAL-COLD warehouse
		pharm_warehouse = frappe.db.get_value(
			"Pharmacy Warehouse",
			{"warehouse_name": "PHARM-CENTRAL-COLD"},
			"erpnext_warehouse"
		)
		
		if not pharm_warehouse:
			return {"success": False, "message": "PHARM-CENTRAL-COLD warehouse not found"}
		
		# Get medication item from prescription
		prescription = frappe.get_doc("GLP-1 Patient Prescription", task_doc.prescription)
		medication = frappe.get_doc("Medication", prescription.medication)
		medication_item = medication.item if hasattr(medication, 'item') else None
		
		if not medication_item:
			return {"success": False, "message": "Medication item not found"}
		
		# Create Stock Entry
		stock_entry = frappe.get_doc({
			"doctype": "Stock Entry",
			"purpose": "Material Issue",
			"items": [{
				"item_code": medication_item,
				"s_warehouse": pharm_warehouse,
				"qty": quantity,
				"batch_no": batch
			}]
		})
		
		# Set patient in custom field if available
		if hasattr(stock_entry, 'custom_patient'):
			stock_entry.custom_patient = task_doc.patient
		
		stock_entry.insert(ignore_permissions=True)
		stock_entry.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Create dispense confirmation
		confirmation = frappe.get_doc({
			"doctype": "GLP-1 Dispense Confirmation",
			"prescription": task_doc.prescription,
			"patient": task_doc.patient,
			"stock_entry": stock_entry.name,
			"batch": batch,
			"pharmacist": frappe.session.user,
			"patient_acknowledgment": patient_acknowledged,
			"counseling_record": counseling_notes
		})
		confirmation.insert(ignore_permissions=True)
		confirmation.submit(ignore_permissions=True)
		frappe.db.commit()
		
		# Update task status
		task_doc.status = "Completed"
		task_doc.save(ignore_permissions=True)
		
		return {"success": True, "stock_entry": stock_entry.name, "confirmation": confirmation.name}
	except Exception as e:
		frappe.log_error(f"Error creating dispense: {str(e)}", "GLP-1 Pharmacist API")
		return {"success": False, "message": str(e)}
