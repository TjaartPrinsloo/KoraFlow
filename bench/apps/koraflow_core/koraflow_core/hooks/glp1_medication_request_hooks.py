# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Medication Request Hooks
Extend Medication Request for GLP-1 specific validations and compliance
"""

import frappe
from frappe import _
from koraflow_core.utils.glp1_compliance import (
	validate_cold_chain_before_dispense,
	create_audit_log
)


def validate_glp1_medication_request(doc, method):
	"""Validate GLP-1 specific rules for Medication Request"""
	if not doc.medication:
		return
	
	# Check if medication is GLP-1
	medication = frappe.get_doc("Medication", doc.medication)
	medication_name = medication.medication_name or medication.name
	
	# Check if it's a GLP-1 medication (simplified check)
	glp1_medications = ["semaglutide", "tirzepatide", "ozempic", "wegovy", "mounjaro", "zepbound"]
	is_glp1 = any(glp1 in str(medication_name).lower() for glp1 in glp1_medications)
	
	if not is_glp1:
		return  # Not a GLP-1 medication
	
	# GLP-1 specific validations
	# 1. Ensure quantity doesn't exceed 30 days
	if doc.quantity and doc.quantity > 30:
		frappe.throw(_("GLP-1 medication quantity cannot exceed 30 days supply per SAHPRA regulations"))
	
	# 2. Ensure batch tracking is enabled for medication item
	if doc.medication_item:
		item = frappe.get_doc("Item", doc.medication_item)
		if not item.has_batch_no:
			frappe.throw(_("GLP-1 medications require batch tracking"))
	
	# 3. Create link to GLP-1 Patient Prescription if available
	if doc.patient:
		# Try to find related prescription
		prescription = frappe.db.get_value(
			"GLP-1 Patient Prescription",
			{"patient": doc.patient, "status": "Doctor Approved"},
			"name",
			order_by="creation desc"
		)
		if prescription and not hasattr(doc, 'glp1_prescription'):
			# Link prescription (if custom field exists)
			pass  # Custom field needs to be added via Customize Form


def on_medication_request_submit(doc, method):
	"""Create audit log when GLP-1 medication request is submitted"""
	if not doc.medication:
		return
	
	medication = frappe.get_doc("Medication", doc.medication)
	medication_name = medication.medication_name or medication.name
	
	glp1_medications = ["semaglutide", "tirzepatide", "ozempic", "wegovy", "mounjaro", "zepbound"]
	is_glp1 = any(glp1 in str(medication_name).lower() for glp1 in glp1_medications)
	
	if is_glp1:
		create_audit_log(
			event_type="Prescription",
			reference_doctype="Medication Request",
			reference_name=doc.name,
			patient=doc.patient,
			actor=frappe.session.user,
			details={"medication": doc.medication, "quantity": doc.quantity}
		)
