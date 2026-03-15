import frappe
from frappe.model.document import Document
from frappe import _


class GLP1IntakeSubmission(Document):
	def validate(self):
		"""Validate uniqueness of ID Number, SA ID, Passport and Mobile"""
		
		# Validate SA ID format if provided
		if getattr(self, 'sa_id_number', None):
			self.validate_sa_id()
		
		# Require at least one form of identification
		has_sa_id = bool(getattr(self, 'sa_id_number', None))
		has_passport = bool(getattr(self, 'passport_number', None))
		has_legacy_id = bool(self.id_number__passport_number)
		
		if not has_sa_id and not has_passport and not has_legacy_id:
			frappe.throw(
				_("Please provide either a South African ID Number or Passport Number"),
				title=_("Identification Required")
			)
		
		# If passport provided, country is required
		if has_passport and not getattr(self, 'passport_country', None):
			frappe.throw(
				_("Please select the country that issued your passport"),
				title=_("Passport Country Required")
			)
		
		# Check for duplicate SA ID Number
		if has_sa_id:
			existing_sa_id = frappe.db.sql("""
				SELECT DISTINCT parent
				FROM `tabGLP-1 Intake Submission`
				WHERE sa_id_number = %s
				AND name != %s
				LIMIT 1
			""", (self.sa_id_number, self.name), as_dict=True)
			
			if existing_sa_id:
				frappe.throw(
					_("South African ID Number {0} is already registered.").format(
						frappe.bold(self.sa_id_number)
					),
					title=_("Duplicate SA ID Number")
				)
		
		# Check for duplicate Passport Number
		if has_passport:
			existing_passport = frappe.db.sql("""
				SELECT DISTINCT parent
				FROM `tabGLP-1 Intake Submission`
				WHERE passport_number = %s
				AND name != %s
				LIMIT 1
			""", (self.passport_number, self.name), as_dict=True)
			
			if existing_passport:
				frappe.throw(
					_("Passport Number {0} is already registered.").format(
						frappe.bold(self.passport_number)
					),
					title=_("Duplicate Passport Number")
				)
		
		# Legacy: Check for duplicate ID Number (only if provided)
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
	
	def validate_sa_id(self):
		"""Validate South African ID Number format and checksum (Luhn algorithm)"""
		sa_id = self.sa_id_number
		
		# Check length
		if len(sa_id) != 13:
			frappe.throw(
				_("South African ID Number must be exactly 13 digits. You entered {0} digits.").format(len(sa_id)),
				title=_("Invalid SA ID Format")
			)
		
		# Check all digits
		if not sa_id.isdigit():
			frappe.throw(
				_("South African ID Number must contain only numbers."),
				title=_("Invalid SA ID Format")
			)
		
		# Extract components
		try:
			yy = int(sa_id[0:2])
			mm = int(sa_id[2:4])
			dd = int(sa_id[4:6])
			
			# Validate month
			if mm < 1 or mm > 12:
				frappe.throw(
					_("Invalid month in SA ID Number. Month should be between 01 and 12."),
					title=_("Invalid SA ID Format")
				)
			
			# Validate day (rough check)
			if dd < 1 or dd > 31:
				frappe.throw(
					_("Invalid day in SA ID Number. Day should be between 01 and 31."),
					title=_("Invalid SA ID Format")
				)
		except ValueError:
			frappe.throw(
				_("Invalid date format in SA ID Number."),
				title=_("Invalid SA ID Format")
			)
		
		# Luhn algorithm check
		total = 0
		for i, digit in enumerate(sa_id):
			d = int(digit)
			if i % 2 == 1:  # Odd position (0-indexed, so 1,3,5,7,9,11)
				d *= 2
				if d > 9:
					d -= 9
			total += d
		
		if total % 10 != 0:
			frappe.throw(
				_("Invalid South African ID Number. Please check and re-enter your ID."),
				title=_("Invalid SA ID Number")
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
			frappe.log_error(title="GLP-1 Intake Submission Error", message="No user email found for intake form submission")
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
				frappe.log_error(title="GLP-1 Intake Submission Error", message=f"Failed to create patient from intake: {error_msg}")
		except Exception as e:
			frappe.log_error(title="GLP-1 Intake Submission Error", message=f"Error processing intake form submission: {str(e)}")
			import traceback
			frappe.log_error(title="GLP-1 Intake Submission Error Traceback", message=traceback.format_exc())
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

