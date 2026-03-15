# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Compliance Checkpoints
Implements all 6 global compliance checkpoints (CP-A through CP-F)
"""

import frappe
from frappe import _
from frappe.utils import now
import json


def create_audit_log(event_type, reference_doctype=None, reference_name=None, 
                     patient=None, actor=None, actor_license=None, details=None):
	"""Create immutable audit log entry"""
	try:
		audit_log = frappe.get_doc({
			"doctype": "GLP-1 Compliance Audit Log",
			"event_type": event_type,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"patient": patient,
			"actor": actor or frappe.session.user,
			"actor_license": actor_license,
			"timestamp": now(),
			"details": json.dumps(details) if details else None
		})
		audit_log.insert(ignore_permissions=True)
		frappe.db.commit()
		return audit_log.name
	except Exception as e:
		frappe.log_error(title="GLP-1 Compliance", message=f"Error creating audit log: {str(e)}")
		return None


# CP-A: Prescription Lock
def check_prescription_lock(prescription_name):
	"""CP-A: Ensure prescription cannot be edited after dispensing"""
	prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
	
	if prescription.status in ["Dispensed", "Closed"]:
		# Check if any dispense confirmations exist
		dispense_exists = frappe.db.exists("GLP-1 Dispense Confirmation", {"prescription": prescription_name})
		if dispense_exists:
			return {
				"locked": True,
				"message": _("Prescription is locked - dispensing has occurred")
			}
	
	return {"locked": False}


def validate_prescription_immutable(prescription, old_doc=None):
	"""Validate prescription fields cannot be changed after approval"""
	if prescription.status in ["Doctor Approved", "Dispensed", "Closed"]:
		if old_doc:
			immutable_fields = ["patient", "medication", "dosage", "quantity", "doctor"]
			for field in immutable_fields:
				if hasattr(old_doc, field) and getattr(old_doc, field) != getattr(prescription, field):
					frappe.throw(_("Cannot modify {0} after prescription approval").format(field))


# CP-B: Batch Traceability
def get_batch_traceability(batch_name):
	"""CP-B: Get complete traceability for a batch in <30 seconds"""
	try:
		# Get batch details
		batch = frappe.get_doc("Batch", batch_name)
		
		# Get compounding records
		compounding_records = frappe.get_all(
			"GLP-1 Compounding Record",
			filters={"source_batch": batch_name},
			fields=["name", "compound_date", "responsible_pharmacist", "pharmacist_license", "patient"]
		)
		
		# Get dispense confirmations
		dispense_confirmations = frappe.get_all(
			"GLP-1 Dispense Confirmation",
			filters={"batch": batch_name},
			fields=["name", "patient", "pharmacist", "stock_entry", "prescription"]
		)
		
		# Get stock entries
		stock_entries = frappe.get_all(
			"Stock Entry",
			filters={"batch_no": batch_name},
			fields=["name", "posting_date", "purpose"]
		)
		
		# Get cold chain logs
		cold_chain_logs = frappe.get_all(
			"GLP-1 Cold Chain Log",
			filters={"batch": batch_name},
			fields=["check_time", "temperature", "excursion", "excursion_resolved"]
		)
		
		return {
			"batch": batch_name,
			"expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
			"compounding_records": compounding_records,
			"dispense_confirmations": dispense_confirmations,
			"stock_entries": stock_entries,
			"cold_chain_logs": cold_chain_logs,
			"traceability_complete": True
		}
	except Exception as e:
		frappe.log_error(title="GLP-1 Compliance", message=f"Error getting batch traceability: {str(e)}")
		return {"error": str(e)}


# CP-C: Cold Chain Enforcement
def check_cold_chain_compliance(batch_name):
	"""CP-C: Check if batch has unresolved temperature excursions"""
	unresolved_excursions = frappe.get_all(
		"GLP-1 Cold Chain Log",
		filters={
			"batch": batch_name,
			"excursion": 1,
			"excursion_resolved": 0
		},
		fields=["name", "check_time", "temperature", "notes"]
	)
	
	if unresolved_excursions:
		return {
			"compliant": False,
			"block_dispensing": True,
			"excursions": unresolved_excursions,
			"message": _("Unresolved temperature excursions exist for this batch")
		}
	
	return {"compliant": True, "block_dispensing": False}


def validate_cold_chain_before_dispense(batch_name):
	"""Validate cold chain before allowing dispense"""
	compliance = check_cold_chain_compliance(batch_name)
	if not compliance["compliant"]:
		frappe.throw(_("Cannot dispense batch {0}: {1}").format(
			batch_name, compliance["message"]
		))


# CP-D: Role Isolation
def check_role_isolation(user, doctype, field=None):
	"""CP-D: Enforce role-based access restrictions"""
	user_roles = frappe.get_roles(user)
	
	# Doctors: cannot see stock quantities
	if "Healthcare Practitioner" in user_roles and doctype == "Warehouse":
		return {"allowed": False, "reason": "Doctors cannot access stock quantities"}
	
	# Sales/Promoters: cannot see prescriptions
	if "Sales Agent" in user_roles or "Sales Partner" in user_roles:
		if doctype in ["GLP-1 Patient Prescription", "GLP-1 Intake Review"]:
			return {"allowed": False, "reason": "Sales roles cannot access prescriptions"}
	
	# Clinics: cannot trigger stock movement
	if "Clinic Admin" in user_roles:
		if doctype == "Stock Entry":
			return {"allowed": False, "reason": "Clinics cannot trigger stock movement"}
	
	return {"allowed": True}


# CP-E: Anti-Wholesaling Guard
def validate_patient_reference(doctype, docname):
	"""CP-E: Ensure every dispense references a patient"""
	if doctype == "Stock Entry":
		stock_entry = frappe.get_doc("Stock Entry", docname)
		
		# Check if this is a GLP-1 dispense
		if stock_entry.purpose == "Material Issue":
			# Check for patient reference in custom fields or linked documents
			patient = None
			
			# Try to get from custom field
			if hasattr(stock_entry, 'custom_patient'):
				patient = stock_entry.custom_patient
			
			# Try to get from linked dispense confirmation
			if not patient:
				dispense_conf = frappe.db.get_value(
					"GLP-1 Dispense Confirmation",
					{"stock_entry": docname},
					"patient"
				)
				if dispense_conf:
					patient = dispense_conf
			
			if not patient:
				frappe.throw(_("Stock Entry for GLP-1 dispense must reference a patient (CP-E: Anti-Wholesaling Guard)"))
			
			return {"patient": patient, "valid": True}
	
	return {"valid": True}


# CP-F: SAHPRA Audit Mode
def generate_sahpra_audit_report(start_date, end_date):
	"""CP-F: Generate SAHPRA audit report"""
	try:
		# Get all dispenses in period
		dispenses = frappe.get_all(
			"GLP-1 Dispense Confirmation",
			filters={
				"creation": ["between", [start_date, end_date]]
			},
			fields=["name", "patient", "prescription", "batch", "pharmacist", "stock_entry"]
		)
		
		# Get patient counts
		unique_patients = len(set([d.patient for d in dispenses if d.patient]))
		
		# Get pharmacist involvement
		unique_pharmacists = len(set([d.pharmacist for d in dispenses if d.pharmacist]))
		
		# Get compounded vs pre-packed
		compounded = frappe.get_all(
			"GLP-1 Compounding Record",
			filters={
				"compound_date": ["between", [start_date, end_date]]
			},
			fields=["name"]
		)
		
		# Calculate quantities
		total_quantity = 0
		for dispense in dispenses:
			if dispense.stock_entry:
				stock_entry = frappe.get_doc("Stock Entry", dispense.stock_entry)
				for item in stock_entry.items:
					total_quantity += item.qty or 0
		
		return {
			"period": {"start": start_date, "end": end_date},
			"total_dispenses": len(dispenses),
			"unique_patients": unique_patients,
			"unique_pharmacists": unique_pharmacists,
			"compounded_count": len(compounded),
			"pre_packed_count": len(dispenses) - len(compounded),
			"total_quantity": total_quantity,
			"dispenses": dispenses
		}
	except Exception as e:
		frappe.log_error(title="GLP-1 Compliance", message=f"Error generating SAHPRA audit report: {str(e)}")
		return {"error": str(e)}


# Utility function to check all checkpoints
def validate_all_checkpoints(doctype, docname, operation="submit"):
	"""Validate all compliance checkpoints before operation"""
	errors = []
	
	# CP-A: Prescription Lock
	if doctype == "GLP-1 Patient Prescription":
		lock_check = check_prescription_lock(docname)
		if lock_check["locked"]:
			errors.append(lock_check["message"])
	
	# CP-C: Cold Chain (for batches)
	if doctype == "Stock Entry":
		stock_entry = frappe.get_doc("Stock Entry", docname)
		for item in stock_entry.items:
			if item.batch_no:
				cold_chain = check_cold_chain_compliance(item.batch_no)
				if not cold_chain["compliant"]:
					errors.append(cold_chain["message"])
	
	# CP-E: Anti-Wholesaling
	if doctype == "Stock Entry":
		patient_check = validate_patient_reference(doctype, docname)
		if not patient_check.get("valid"):
			errors.append("Patient reference required for GLP-1 dispense")
	
	if errors:
		frappe.throw("\n".join(errors))
