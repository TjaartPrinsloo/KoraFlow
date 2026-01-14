import frappe
from frappe.model.document import Document
from frappe import _


class GLP1IntakeSubmission(Document):
	def validate(self):
		"""Validate uniqueness of ID Number and Mobile"""
		# Check for duplicate ID Number (only if provided)
		if self.id_number__passport_number:
			# Since this is a child table, we need to check across all parent records
			# Query all GLP-1 Intake Submission records with this ID number
			existing = frappe.db.sql("""
				SELECT DISTINCT parent
				FROM `tabGLP-1 Intake Submission`
				WHERE id_number__passport_number = %s
				AND name != %s
				LIMIT 1
			""", (self.id_number__passport_number, self.name), as_dict=True)
			
			if existing:
				frappe.throw(
					_("ID Number / Passport Number {0} is already registered. Please use a different ID Number.").format(
						frappe.bold(self.id_number__passport_number)
					),
					title=_("Duplicate ID Number")
				)
		
		# Check for duplicate Mobile (only if mobile is provided)
		if self.mobile:
			# Check in GLP-1 Intake Submission (child table)
			existing_intake = frappe.db.sql("""
				SELECT DISTINCT parent
				FROM `tabGLP-1 Intake Submission`
				WHERE mobile = %s
				AND name != %s
				LIMIT 1
			""", (self.mobile, self.name), as_dict=True)
			
			if existing_intake:
				frappe.throw(
					_("Mobile number {0} is already registered. Please use a different mobile number.").format(
						frappe.bold(self.mobile)
					),
					title=_("Duplicate Mobile Number")
				)
			
			# Also check in Patient DocType
			existing_patient = frappe.db.get_value(
				"Patient",
				{"mobile": self.mobile},
				"name"
			)
			if existing_patient:
				frappe.throw(
					_("Mobile number {0} is already registered to another patient. Please use a different mobile number.").format(
						frappe.bold(self.mobile)
					),
					title=_("Duplicate Mobile Number")
				)
	
	def after_insert(self):
		"""After intake form is submitted, create Patient and child table record"""
		frappe.logger().info(f"[GLP1IntakeSubmission.after_insert] Hook called for {self.name}")
		
		from koraflow_core.api.patient_signup import create_patient_from_intake
		
		# Get user email - prioritize logged-in user over form email
		# This ensures we use the actual logged-in user's email, not what they typed in the form
		if frappe.session.user and frappe.session.user != "Guest":
			user_email = frappe.session.user
		else:
			user_email = self.email
		
		frappe.logger().info(f"[GLP1IntakeSubmission.after_insert] Using user_email: {user_email}")
		
		if not user_email or user_email == "Guest":
			frappe.log_error("No user email found for intake form submission", "GLP-1 Intake Submission Error")
			return
		
		# Convert submission data to intake_data format
		intake_data = self.as_dict()
		
		# Ensure email is set in intake_data
		if not intake_data.get('email'):
			intake_data['email'] = user_email
		
		try:
			# Create patient and intake form child record
			result = create_patient_from_intake(intake_data, user_email=user_email)
			
			if result and result.get('success'):
				frappe.logger().info(f"Intake form submitted for {user_email}, patient: {result.get('patient')}, intake_form: {result.get('intake_form')}")
				# Commit to ensure data is saved
				frappe.db.commit()
			else:
				error_msg = result.get('message') if isinstance(result, dict) else str(result)
				frappe.log_error(f"Failed to create patient from intake: {error_msg}", "GLP-1 Intake Submission Error")
		except Exception as e:
			frappe.log_error(f"Error processing intake form submission: {str(e)}", "GLP-1 Intake Submission Error")
			import traceback
			frappe.log_error(traceback.format_exc(), "GLP-1 Intake Submission Error Traceback")
			# Don't raise - allow the submission to be saved even if processing fails
	
	def on_submit(self):
		"""Create intake review when intake is submitted"""
		# Check if review already exists
		existing_review = frappe.db.exists("GLP-1 Intake Review", {"intake_submission": self.name})
		if not existing_review:
			review = frappe.get_doc({
				"doctype": "GLP-1 Intake Review",
				"intake_submission": self.name,
				"status": "Pending"
			})
			review.insert(ignore_permissions=True)
			frappe.db.commit()

