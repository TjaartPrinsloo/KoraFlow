"""
Prescription Generation Hooks
Automatically generate and attach prescription PDFs when encounters with medications are submitted
"""
import frappe
from frappe import _

from koraflow_core.utils.prescription_generator import generate_and_attach_prescription


def generate_prescription_on_encounter_submit(doc, method):
	"""
	Hook function called when Patient Encounter is submitted.
	Generates and attaches prescription PDF if encounter contains medications.
	
	Args:
		doc: Patient Encounter document
		method: Hook method name (e.g., 'on_submit')
	"""
	# Only generate prescription if encounter has medications
	if not doc.drug_prescription:
		return
	
	# Only generate if encounter is being submitted (not saved)
	if doc.docstatus != 1:
		return
	
	# Check if patient exists
	if not doc.patient:
		frappe.logger().warning(f"Encounter {doc.name} has no patient. Skipping prescription generation.")
		return
	
	# Check if practitioner exists
	if not doc.practitioner:
		frappe.logger().warning(f"Encounter {doc.name} has no practitioner. Skipping prescription generation.")
		return
	
	try:
		# Generate and attach prescription
		file_doc = generate_and_attach_prescription(doc)
		
		if file_doc:
			frappe.msgprint(
				_("Prescription PDF has been generated and attached to patient profile."),
				indicator="green",
				title=_("Prescription Generated")
			)
			frappe.logger().info(
				f"Prescription PDF generated and attached for encounter {doc.name}, patient {doc.patient}"
			)
		else:
			frappe.logger().warning(
				f"Prescription generation returned None for encounter {doc.name}"
			)
			
	except Exception as e:
		# Log error but don't block encounter submission
		error_msg = str(e)
		frappe.log_error(
			message=f"Error generating prescription for encounter {doc.name}: {error_msg}",
			title="Prescription Generation Error",
			reference_doctype="Patient Encounter",
			reference_name=doc.name
		)
		
		# Provide helpful error message
		if "wkhtmltopdf" in error_msg or "weasyprint" in error_msg or "system dependencies" in error_msg.lower():
			user_msg = _(
				"Prescription PDF generation requires PDF system dependencies. "
				"The encounter was submitted successfully, but the prescription PDF could not be generated. "
				"Please install wkhtmltopdf or weasyprint dependencies, or contact your system administrator."
			)
		else:
			user_msg = _("Warning: Prescription PDF could not be generated. Please check error log.")
		
		# Show warning to user but don't throw exception (don't block encounter submission)
		frappe.msgprint(
			user_msg,
			indicator="orange",
			title=_("Prescription Generation Warning")
		)
