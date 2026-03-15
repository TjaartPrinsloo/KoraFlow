"""
Patient Prescriptions Page
Shows all prescriptions for a patient
"""
import frappe
from frappe import _


def get_context(context):
	"""Get context for patient prescriptions page"""
	context.no_cache = 1
	
	# Get patient from route options, form_dict, or query string
	patient = None
	
	# Try route_options first (from frappe.set_route)
	if hasattr(frappe.local, 'route_options') and frappe.local.route_options:
		patient = frappe.local.route_options.get('patient')
	
	# Try form_dict
	if not patient and hasattr(frappe.local, 'form_dict') and frappe.local.form_dict:
		patient = frappe.local.form_dict.get('patient')
	
	# Try request args
	if not patient and hasattr(frappe.local, 'request') and frappe.local.request:
		patient = frappe.local.request.args.get('patient')
	
	if not patient:
		frappe.throw(_("Patient is required"), frappe.ValidationError)
	
	# Verify patient exists
	if not frappe.db.exists('Patient', patient):
		frappe.throw(_("Patient not found"), frappe.DoesNotExistError)
	
	patient_doc = frappe.get_doc('Patient', patient)
	context.patient = patient_doc
	
	# Get prescriptions
	try:
		from koraflow_core.api.patient_prescriptions import get_patient_prescriptions
		prescriptions_data = get_patient_prescriptions(patient)
	except Exception as e:
		frappe.log_error(title="Web Prescription Fetch Error", message=f"Error getting prescriptions: {str(e)}")
		prescriptions_data = {'prescriptions': [], 'count': 0}
	context.prescriptions = prescriptions_data.get('prescriptions', [])
	context.prescription_count = prescriptions_data.get('count', 0)
	
	# Page title
	context.title = _("Prescriptions - {0}").format(patient_doc.patient_name or patient)
