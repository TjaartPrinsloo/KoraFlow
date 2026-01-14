"""
API for Patient Prescriptions
Returns all prescription files for a patient
"""
import frappe
from frappe import _


@frappe.whitelist()
def get_patient_prescriptions(patient):
	"""
	Get all prescription files for a patient
	
	Args:
		patient: Patient name
		
	Returns:
		List of prescription file details
	"""
	if not patient:
		frappe.throw(_("Patient is required"))
	
	# Get all files attached to the patient that are prescriptions
	# Prescription files are named like "Prescription_HLC-ENC-XXXXX_YYYY-MM-DD.pdf"
	prescription_files = frappe.get_all(
		'File',
		filters={
			'attached_to_doctype': 'Patient',
			'attached_to_name': patient,
			'file_name': ['like', 'Prescription_%']
		},
		fields=['name', 'file_name', 'file_url', 'creation', 'modified'],
		order_by='creation desc'
	)
	
	# Also check for files attached via Patient Encounter
	encounters = frappe.get_all(
		'Patient Encounter',
		filters={'patient': patient},
		fields=['name']
	)
	
	encounter_prescriptions = []
	if encounters:
		encounter_names = [e.name for e in encounters]
		encounter_prescriptions = frappe.get_all(
			'File',
			filters={
				'attached_to_doctype': 'Patient Encounter',
				'attached_to_name': ['in', encounter_names],
				'file_name': ['like', 'Prescription_%']
			},
			fields=['name', 'file_name', 'file_url', 'creation', 'modified', 'attached_to_name'],
			order_by='creation desc'
		)
	
	# Combine and format results
	all_prescriptions = []
	
	for file in prescription_files:
		all_prescriptions.append({
			'file_name': file.file_name,
			'file_url': file.file_url,
			'creation': file.creation,
			'modified': file.modified,
			'encounter': None
		})
	
	for file in encounter_prescriptions:
		all_prescriptions.append({
			'file_name': file.file_name,
			'file_url': file.file_url,
			'creation': file.creation,
			'modified': file.modified,
			'encounter': file.attached_to_name
		})
	
	# Sort by creation date (newest first)
	all_prescriptions.sort(key=lambda x: x['creation'], reverse=True)
	
	return {
		'prescriptions': all_prescriptions,
		'count': len(all_prescriptions)
	}
