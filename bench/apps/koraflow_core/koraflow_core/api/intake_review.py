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
	
	# Parse intake_data if it's a string
	if isinstance(intake_data, str):
		intake_data = frappe.parse_json(intake_data)
	
	# Ensure email is set in intake_data
	if not intake_data.get('email'):
		intake_data['email'] = user_email

	try:
		# We pass the intake_data directly to create_patient_from_intake
		# It will handle mapping key patient fields (dob/sex) internally
		# and dynamically catch all submission fields.
		result = create_patient_from_intake(intake_data, user_email=user_email)

		if result and result.get('success'):
			# Success! Now create the first Patient Vital record so the dashboard is populated
			try:
				patient_name = result.get('patient')
				weight = intake_data.get('intake_weight_kg')
				height = intake_data.get('intake_height_cm')
				
				if patient_name and weight:
					from koraflow_core.www.dashboard import submit_vital
					# We need to spoof the session for submit_vital if it uses frappe.session.user
					# But since we are already in a whitelisted context as the user, it should just work.
					submit_vital(weight, height)
                    
					# Reset retake flag
					frappe.db.set_value("Patient", patient_name, "custom_allow_intake_retake", 0)
					
					frappe.db.commit()
			except Exception as ve:
				frappe.log_error(message=f"Error creating initial vital: {str(ve)}", title="Intake Vital Error")

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
		frappe.log_error(message=f"Error creating intake submission: {str(e)}", title="Intake Submission Error")
		return {
			"success": False,
			"message": _("Error submitting intake form. Please try again or contact support.")
		}

