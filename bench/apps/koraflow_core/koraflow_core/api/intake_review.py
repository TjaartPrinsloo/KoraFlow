"""
API endpoints for medical staff to review and activate patient intake forms
"""
import frappe
from frappe import _


@frappe.whitelist()
def review_intake_form(intake_form_name, form_status="Reviewed"):
	"""
	Medical staff can review an intake form and change its status
	When status is changed to "Reviewed", the patient user is activated
	
	Args:
		intake_form_name: Name of the GLP-1 Intake Form child table entry
		form_status: New status (should be "Reviewed" to activate patient)
	"""
	# Check permissions - only medical staff should be able to review
	if not frappe.has_permission("Patient", "write"):
		frappe.throw(_("You do not have permission to review intake forms"), frappe.PermissionError)
	
	# Get the intake form
	# It's a child table, so we need to query it differently
	intake_form = frappe.db.get_value(
		"GLP-1 Intake Form",
		{"name": intake_form_name},
		["name", "parent", "form_status"],
		as_dict=True
	)
	
	if not intake_form:
		frappe.throw(_("Intake form not found"), frappe.DoesNotExistError)
	
	# Get parent Patient
	patient = frappe.get_doc("Patient", intake_form.parent)
	
	# Find the intake form in the child table
	intake_form_doc = None
	for form in patient.glp1_intake_forms:
		if form.name == intake_form_name:
			intake_form_doc = form
			break
	
	if not intake_form_doc:
		frappe.throw(_("Intake form not found in patient record"), frappe.DoesNotExistError)
	
	# Update form status
	old_status = intake_form_doc.form_status
	intake_form_doc.form_status = form_status
	
	# Save patient record
	patient.flags.ignore_permissions = True
	patient.save()
	frappe.db.commit()
	
	# If status changed to "Reviewed", activate the user
	if form_status == "Reviewed" and old_status != "Reviewed":
		from koraflow_core.workflows.intake_review_workflow import on_intake_form_update
		# Reload the form doc to get updated status
		patient.reload()
		for form in patient.glp1_intake_forms:
			if form.name == intake_form_name:
				on_intake_form_update(form, None)
				break
	
	return {
		"success": True,
		"message": _("Intake form status updated to {0}").format(form_status),
		"form_status": form_status
	}


@frappe.whitelist()
def get_intake_forms_for_review():
	"""
	Get all intake forms with status "Under Review" for medical staff to review
	"""
	# Check permissions
	if not frappe.has_permission("Patient", "read"):
		frappe.throw(_("You do not have permission to view intake forms"), frappe.PermissionError)
	
	# Query all intake forms with status "Under Review"
	# Since it's a child table, we need to query via Patient
	patients = frappe.get_all(
		"Patient",
		filters={"status": "Under Review"},
		fields=["name", "first_name", "last_name", "email", "status"]
	)
	
	forms_for_review = []
	for patient in patients:
		patient_doc = frappe.get_doc("Patient", patient.name)
		for form in patient_doc.glp1_intake_forms:
			if form.form_status == "Under Review":
				forms_for_review.append({
					"intake_form_name": form.name,
					"patient_name": patient.name,
					"patient_full_name": f"{patient.first_name} {patient.last_name}".strip(),
					"patient_email": patient.email,
					"form_status": form.form_status,
					"completion_date": form.completion_date
				})
	
	return {
		"forms": forms_for_review,
		"count": len(forms_for_review)
	}


@frappe.whitelist()
def create_intake_submission(intake_data):
	"""
	Create GLP-1 Intake Submission from wizard form data
	This method processes the intake form data and creates/updates the Patient record
	"""
	from koraflow_core.api.patient_signup import create_patient_from_intake
	
	# Get user email from session
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to submit the intake form"), frappe.PermissionError)
	
	user_email = frappe.session.user
	
	# Ensure email is set in intake_data
	if not intake_data.get('email'):
		intake_data['email'] = user_email
	
	# Map wizard field names to intake submission field names
	# The wizard uses different field names (e.g., legal_name vs first_name/last_name)
	field_mapping = {
		'legal_name': 'first_name',  # Will need to split this
		'date_of_birth': 'dob',
		'biological_sex': 'sex',
		'height_unit': 'intake_height_unit',
		'height_feet': 'intake_height_feet',
		'height_inches': 'intake_height_inches',
		'height_cm': 'intake_height_cm',
		'weight_unit': 'intake_weight_unit',
		'weight_pounds': 'intake_weight_pounds',
		'weight_kg': 'intake_weight_kg',
		'blood_pressure_systolic': 'intake_bp_systolic',
		'blood_pressure_diastolic': 'intake_bp_diastolic',
		'resting_heart_rate': 'intake_heart_rate',
		'medullary_thyroid_carcinoma': 'intake_mtc',
		'men2_syndrome': 'intake_men2',
		'pancreatitis_history': 'intake_pancreatitis',
		'gallstones_history': 'intake_gallstones',
		'gallbladder_removal': 'intake_gallbladder_removal',
		'gastroparesis': 'intake_gastroparesis',
		'frequent_nausea': 'intake_frequent_nausea',
		'early_fullness': 'intake_early_fullness',
		'kidney_disease_history': 'intake_kidney_disease',
		'egfr': 'intake_egfr',
		'creatinine': 'intake_creatinine',
		'diabetic_retinopathy': 'intake_diabetic_retinopathy',
		'last_dilated_eye_exam': 'intake_last_eye_exam',
		'heart_attack_history': 'intake_heart_attack',
		'stroke_history': 'intake_stroke',
		'heart_failure_history': 'intake_heart_failure',
		'taking_insulin': 'intake_taking_insulin',
		'taking_sulfonylureas': 'intake_taking_sulfonylureas',
		'insulin_sulfonylurea_dose': 'intake_insulin_dose',
		'narrow_therapeutic_window_drugs': 'intake_narrow_window_drugs',
		'medications_used_ozempic': 'intake_med_ozempic',
		'medications_used_wegovy': 'intake_med_wegovy',
		'medications_used_mounjaro': 'intake_med_mounjaro',
		'medications_used_zepbound': 'intake_med_zepbound',
		'highest_dose_reached': 'intake_highest_dose',
		'last_dose_date': 'intake_last_dose_date',
		'side_effects_nausea': 'intake_se_nausea',
		'side_effects_vomiting': 'intake_se_vomiting',
		'side_effects_diarrhea': 'intake_se_diarrhea',
		'side_effects_constipation': 'intake_se_constipation',
		'side_effects_reflux': 'intake_se_reflux',
		'side_effects_severity': 'intake_se_severity',
		'scoff_question_1': 'intake_scoff_1',
		'scoff_question_2': 'intake_scoff_2',
		'scoff_question_3': 'intake_scoff_3',
		'scoff_question_4': 'intake_scoff_4',
		'scoff_question_5': 'intake_scoff_5',
		'motivation_health': 'intake_motivation_health',
		'motivation_appearance': 'intake_motivation_appearance',
		'motivation_mobility': 'intake_motivation_mobility',
		'goal_weight': 'intake_goal_weight',
		'pregnant': 'intake_pregnant',
		'breastfeeding': 'intake_breastfeeding',
		'planning_to_conceive': 'intake_planning_conceive'
	}
	
	# Map fields
	mapped_data = {}
	for key, value in intake_data.items():
		if key in field_mapping:
			mapped_data[field_mapping[key]] = value
		else:
			mapped_data[key] = value
	
	# Handle legal_name -> first_name/last_name split
	if 'legal_name' in intake_data and intake_data['legal_name']:
		legal_name = intake_data['legal_name'].strip()
		name_parts = legal_name.split(' ', 1)
		mapped_data['first_name'] = name_parts[0]
		if len(name_parts) > 1:
			mapped_data['last_name'] = name_parts[1]
		else:
			mapped_data['last_name'] = ''
	
	# Ensure email is set
	mapped_data['email'] = user_email
	
	try:
		# Create patient and intake form
		result = create_patient_from_intake(mapped_data, user_email=user_email)
		
		if result and result.get('success'):
			return {
				"success": True,
				"message": _("Intake form submitted successfully"),
				"patient": result.get('patient'),
				"intake_form": result.get('intake_form')
			}
		else:
			error_msg = result.get('message') if isinstance(result, dict) else str(result)
			return {
				"success": False,
				"message": error_msg or _("Failed to submit intake form")
			}
	except Exception as e:
		frappe.log_error(f"Error creating intake submission: {str(e)}", "Intake Submission Error")
		return {
			"success": False,
			"message": _("Error submitting intake form. Please try again or contact support.")
		}

