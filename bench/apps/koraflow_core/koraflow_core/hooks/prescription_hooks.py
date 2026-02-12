"""
Prescription Generation Hooks
Automatically generate and attach prescription PDFs when encounters with medications are submitted
"""
import frappe
from frappe import _

from koraflow_core.utils.prescription_generator import generate_and_attach_prescription



def handle_encounter_submit(doc, method):
	"""
	Hook function called when Patient Encounter is submitted.
	1. Generates and attaches prescription PDF.
	2. Generates Quotation if medications are prescribed.
	
	Args:
		doc: Patient Encounter document
		method: Hook method name (e.g., 'on_submit')
	"""
	# 1. Generate Prescription PDF
	generate_prescription_pdf(doc)
	
	# 2. Generate Quotation
	generate_quotation_from_encounter(doc)

	# 3. Activate Patient User
	activate_patient_user(doc)


def generate_prescription_pdf(doc):
	"""Generate and attach prescription PDF if encounter contains medications."""
	# Only generate prescription if encounter has medications
	if not doc.drug_prescription:
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


def activate_patient_user(doc):
	"""
	Activate the User linked to the Patient if medications are prescribed.
	"""
	if not doc.drug_prescription:
		return

	if not doc.patient:
		return

	try:
		patient = frappe.get_doc("Patient", doc.patient)
		if patient.user_id:
			user = frappe.get_doc("User", patient.user_id)
			if not user.enabled:
				user.enabled = 1
				user.save(ignore_permissions=True)
				frappe.msgprint(
					_("User account {0} has been activated.").format(user.name),
					indicator="green",
					title=_("User Activated")
				)
	except Exception as e:
		frappe.log_error(
			message=f"Error activating user for patient {doc.patient}: {str(e)}",
			title="User Activation Error"
		)



def generate_quotation_from_encounter(doc):
	"""
	Generate a Quotation from the medications in the Patient Encounter.
	"""
	if not doc.drug_prescription:
		return

	try:
		patient = frappe.get_doc("Patient", doc.patient)
		if not patient.customer:
			# Create customer if missing
			customer = frappe.new_doc("Customer")
			customer.customer_name = patient.patient_name
			customer.customer_type = "Individual"
			customer.customer_group = "Individual"
			customer.save(ignore_permissions=True)
			
			# Link to patient
			patient.customer = customer.name
			patient.save(ignore_permissions=True)

		# Get Practitioner for details
		practitioner = None
		doctor_reg = "N/A"
		if doc.practitioner:
			practitioner = frappe.get_doc("Healthcare Practitioner", doc.practitioner)
			# Try different fields for registration number
			if hasattr(practitioner, 'hpcsa_registration_number'):
				doctor_reg = practitioner.hpcsa_registration_number
			elif hasattr(practitioner, 'registration_number'):
				doctor_reg = practitioner.registration_number
			elif hasattr(practitioner, 'practice_number'):
				doctor_reg = practitioner.practice_number

		items = []
		primary_prescription = None
		
		for drug in doc.drug_prescription:
			# Get Item from Medication (Child Table: linked_items)
			linked_item = frappe.get_all("Medication Linked Item", filters={"parent": drug.medication}, fields=["item"], limit=1)
			
			# Create GLP-1 Patient Prescription
			try:
				pres = frappe.new_doc("GLP-1 Patient Prescription")
				pres.patient = doc.patient
				pres.doctor = doc.practitioner
				pres.doctor_registration_number = doctor_reg or "N/A"
				pres.medication = drug.medication
				pres.dosage = str(drug.dosage) if drug.dosage else "As directed"
				pres.duration = str(drug.period) if drug.period else "1 Month" 
				pres.quantity = 1 # Default, or calculate logic
				pres.prescription_date = doc.encounter_date or frappe.utils.today()
				pres.status = "Doctor Approved" # Auto-approve as it comes from Doctor's encounter
				pres.diagnosis = getattr(doc, 'diagnosis', '') or "Weight Management"
				pres.save(ignore_permissions=True)
				
				if not primary_prescription:
					primary_prescription = pres.name
			except Exception as e:
				frappe.logger().error(f"Failed to create GLP-1 Prescription for encounter {doc.name}: {str(e)}")
				pres = None

			if linked_item and linked_item[0].item:
				item_code = linked_item[0].item
				
				# Get Price
				price_list_rate = 0
				item_price = frappe.get_all("Item Price", 
					filters={"item_code": item_code, "price_list": "Standard Selling"}, 
					fields=["price_list_rate"], 
					limit=1
				)
				if item_price:
					price_list_rate = item_price[0].price_list_rate

				item_dict = {
					"item_code": item_code,
					"qty": 1, 
					"rate": price_list_rate
				}
				
				# Link specific prescription to item
				if pres:
					item_dict["custom_prescription"] = pres.name
					
				items.append(item_dict)
			else:
				frappe.msgprint(_("Warning: No Linked Item found for Medication {0}. Skipping in Quotation.").format(drug.medication))

		if not items:
			return

		# Create Quotation
		qt = frappe.new_doc("Quotation")
		qt.quotation_to = "Customer"
		qt.party_name = patient.customer
		qt.transaction_date = frappe.utils.today()
		qt.order_type = "Sales"
		qt.company = doc.company or frappe.defaults.get_user_default("Company")
		
		# Add items
		for item in items:
			qt.append("items", item)
			
		# Link to Encounter (using title as fallback if custom field doesn't exist)
		qt.title = f"Prescription: {doc.name}"
		
		# Set Custom Fields for Referral and Prescription Link
		# Link the PRIMARY prescription to the main doc field (for backward compatibility/main validation)
		if primary_prescription:
			qt.custom_prescription = primary_prescription
		else:
			# Fallback: DO NOT link encounter here as it causes validation error
			pass
			
		if hasattr(patient, 'custom_referrer_name') and patient.custom_referrer_name:
			qt.custom_referrer_name = patient.custom_referrer_name
		
		# Bypass link validation to allow linking to the encounter currently being submitted
		qt.flags.ignore_links = True
		qt.save(ignore_permissions=True)
		
		# Link Quotation back to Prescriptions
		if primary_prescription:
			# Update linked_quotation field on prescriptions
			# We'll just update all created ones for this loop
			for item in items:
				if "custom_prescription" in item:
					frappe.db.set_value("GLP-1 Patient Prescription", item["custom_prescription"], "linked_quotation", qt.name)
		
		frappe.msgprint(
			_("Quotation {0} created successfully.").format(qt.name),
			indicator="green",
			title=_("Quotation Created")
		)

	except Exception as e:
		frappe.log_error(
			message=f"Error generating quotation for encounter {doc.name}: {str(e)}",
			title="Quotation Generation Error"
		)
		frappe.msgprint(
			_("Error creating Quotation. Please check Error Log."),
			indicator="red"
		)

