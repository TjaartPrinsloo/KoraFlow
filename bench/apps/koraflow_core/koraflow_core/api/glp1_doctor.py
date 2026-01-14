# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Doctor API
APIs for doctor prescription interface
"""

import frappe
from frappe import _


@frappe.whitelist()
def check_contraindications(patient, medication):
	"""Check for contraindications for patient and medication"""
	warnings = []
	
	# Get patient intake data
	intake = get_patient_intake_data(patient)
	if not intake:
		return {"contraindications": warnings}
	
	# Check absolute contraindications
	if intake.get("intake_mtc") or intake.get("intake_men2"):
		warnings.append(_("Absolute contraindication: Medullary Thyroid Carcinoma (MTC) or MEN 2"))
	
	# Check relative contraindications
	if intake.get("intake_pancreatitis"):
		warnings.append(_("Warning: History of pancreatitis"))
	
	if intake.get("intake_kidney_disease"):
		warnings.append(_("Warning: History of kidney disease - monitor eGFR"))
	
	if intake.get("intake_pregnant") or intake.get("intake_breastfeeding"):
		warnings.append(_("Warning: Pregnancy or breastfeeding - GLP-1 not recommended"))
	
	return {"contraindications": warnings}


@frappe.whitelist()
def get_patient_intake(patient):
	"""Get patient intake submission data"""
	intake_data = get_patient_intake_data(patient)
	return {"intake": intake_data}


def get_patient_intake_data(patient):
	"""Get latest intake submission for patient"""
	# Find patient's intake submission
	intake_submission = frappe.db.get_value(
		"GLP-1 Intake Submission",
		{"parent": patient},
		"name",
		order_by="creation desc"
	)
	
	if not intake_submission:
		return None
	
	# Get intake data
	intake = frappe.get_doc("GLP-1 Intake Submission", intake_submission)
	return intake.as_dict()
