"""
Workflow for reviewing and activating patient intake forms
When medical staff changes form_status from "Under Review" to "Reviewed",
the patient user is activated and quote is shown
"""
import frappe
from frappe import _


def on_intake_form_update(doc, method):
	"""
	Triggered when GLP-1 Intake Form is updated
	If form_status changes to "Reviewed", activate the patient user
	"""
	if doc.form_status == "Reviewed":
		# Get the parent Patient record
		patient_name = doc.parent
		if not patient_name:
			return
		
		try:
			patient = frappe.get_doc("Patient", patient_name)
			
			# Get user linked to patient
			user_email = patient.user_id or patient.email
			if not user_email:
				frappe.log_error(title="Intake Review Workflow", message=f"No user found for patient {patient_name}")
				return
			
			# Activate the user
			user = frappe.get_doc("User", user_email)
			if not user.enabled:
				user.enabled = 1
				user.flags.ignore_permissions = True
				user.save()
				frappe.db.commit()
				
				frappe.logger().info(f"Activated user {user_email} after intake form review")
				
				# Update patient status to Active
				if patient.status == "Under Review":
					patient.status = "Active"
					patient.flags.ignore_permissions = True
					patient.save()
					frappe.db.commit()
				
				# Send activation email to patient
				try:
					send_activation_email(user, patient)
				except Exception as e:
					frappe.log_error(title="Intake Review Workflow", message=f"Error sending activation email: {str(e)}")
		
		except Exception as e:
			frappe.log_error(title="Intake Review Workflow", message=f"Error activating user for intake form {doc.name}: {str(e)}")


def send_activation_email(user, patient):
	"""Send activation email to patient"""
	from frappe.utils import get_url
	
	# Generate password reset link so they can set their password
	from frappe.core.doctype.user.user import generate_keys
	key = generate_keys(user.name)
	link = get_url(f"/update-password?key={key}&name={user.name}")
	
	subject = _("Your Patient Profile Has Been Activated")
	message = f"""
	<p>Dear {user.first_name},</p>
	
	<p>Your patient profile has been reviewed and activated by our medical staff.</p>
	
	<p>You can now access your patient portal and view your quote.</p>
	
	<p><a href="{link}">Click here to set your password and log in</a></p>
	
	<p>If the link doesn't work, copy and paste this URL into your browser:</p>
	<p>{link}</p>
	
	<p>Best regards,<br>
	KoraFlow Medical Team</p>
	"""
	
	frappe.sendmail(
		recipients=[user.email],
		subject=subject,
		message=message,
		now=True
	)

