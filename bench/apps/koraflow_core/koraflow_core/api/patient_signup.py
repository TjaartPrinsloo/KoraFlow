import frappe
from frappe import _
from frappe.utils import now_datetime, escape_html, random_string, cint, get_url, sha256_hash
from frappe.utils.password import update_password
from frappe.core.doctype.user.user import is_signup_disabled
from koraflow_core.utils.security import mask_email


@frappe.whitelist()
def check_patient_exists(user_email=None):
	"""Check if Patient record exists for the current user or specified email"""
	if not user_email:
		user_email = frappe.session.user
	
	# Check if Patient exists with this email
	patient = frappe.db.get_value("Patient", {"email": user_email}, "name")
	
	return {
		"exists": bool(patient),
		"patient_name": patient
	}


@frappe.whitelist()
def get_intake_form_status(user_email=None):
	"""Check if intake form is completed for a user"""
	if not user_email:
		user_email = frappe.session.user
	
	# Check if Patient exists
	patient = frappe.db.get_value("Patient", {"email": user_email}, "name")
	
	if not patient:
		return {
			"status": "not_started",
			"patient_exists": False
		}
	
	# Check if intake form exists and is completed
	intake_forms = frappe.get_all(
		"GLP-1 Intake Form",
		filters={"parent": patient, "form_status": "Completed"},
		fields=["name", "completion_date"],
		limit=1
	)
	
	if intake_forms:
		return {
			"status": "completed",
			"patient_exists": True,
			"intake_form": intake_forms[0].name,
			"completion_date": intake_forms[0].completion_date
		}
	
	# Check if draft exists
	draft_forms = frappe.get_all(
		"GLP-1 Intake Form",
		filters={"parent": patient, "form_status": "Draft"},
		fields=["name"],
		limit=1
	)
	
	if draft_forms:
		return {
			"status": "draft",
			"patient_exists": True,
			"intake_form": draft_forms[0].name
		}
	
	return {
		"status": "not_started",
		"patient_exists": True
	}


@frappe.whitelist()
def create_patient_from_intake(intake_data, user_email=None):
	"""Create Patient record and GLP-1 Intake Form from intake form data"""
	if not user_email:
		user_email = frappe.session.user
	
	# Get user details - handle case where user might not exist
	if not frappe.db.exists("User", user_email):
		frappe.log_error(f"User {mask_email(user_email)} not found when processing intake form", "GLP-1 Intake Submission Error")
		# Try to get user from email field in intake data
		email_from_data = intake_data.get('email') or intake_data.get('intake_email')
		if email_from_data and frappe.db.exists("User", email_from_data):
			user_email = email_from_data
			frappe.logger().info(f"Using email from intake data: {mask_email(user_email)}")
		else:
			# If no user exists, we can't create the patient properly
			# Log error but don't fail - allow submission to be saved
			frappe.log_error(f"No user found for email {user_email}. Intake form saved but patient not created.", "GLP-1 Intake Submission Error")
			return {
				"success": False,
				"message": f"No user account found for {user_email}. Please contact support.",
				"error": "User not found"
			}
	
	# Get user details
	user = frappe.get_doc("User", user_email)
	
	# Check if Patient already exists
	existing_patient = frappe.db.get_value("Patient", {"email": user_email}, "name")
	
	if existing_patient:
		patient = frappe.get_doc("Patient", existing_patient)
		# Update status to "Disabled" if it was "Active"
		if patient.status == "Active":
			patient.status = "Disabled"
		# Ensure height_unit and weight_unit are set if missing (required fields)
		if hasattr(patient, 'height_unit') and not patient.height_unit:
			patient.height_unit = intake_data.get("height_unit") or intake_data.get("intake_height_unit") or "Feet/Inches"
		if hasattr(patient, 'weight_unit') and not patient.weight_unit:
			patient.weight_unit = intake_data.get("weight_unit") or intake_data.get("intake_weight_unit") or "Pounds"
		# Ensure user_id is set to prevent user creation
		if not patient.user_id:
			patient.user_id = user_email
		patient.flags.skip_user_creation = True  # Prevent user creation hook
	else:
		# Create new Patient record with "Disabled" status
		# Handle both field name formats: web form (first_name/last_name) and intake form (legal_name)
		first_name = intake_data.get("first_name") or (intake_data.get("legal_name", "").split()[0] if intake_data.get("legal_name") else user.first_name)
		last_name = intake_data.get("last_name") or (" ".join(intake_data.get("legal_name", "").split()[1:]) if intake_data.get("legal_name") and len(intake_data.get("legal_name", "").split()) > 1 else user.last_name or "")
		
		# Handle sex/gender field - can be from sex (Link) or biological_sex (Select)
		sex_value = intake_data.get("sex") or intake_data.get("biological_sex")
		if isinstance(sex_value, str):
			# If it's a string, try to get the Gender record
			gender_name = frappe.db.get_value("Gender", {"name": sex_value}, "name") or sex_value
		else:
			gender_name = "Male"  # Default
		
		# Handle date of birth - can be dob or date_of_birth
		dob_value = intake_data.get("dob") or intake_data.get("date_of_birth")
		
		# Get height_unit and weight_unit from intake data
		height_unit = intake_data.get("height_unit") or intake_data.get("intake_height_unit") or "Feet/Inches"
		weight_unit = intake_data.get("weight_unit") or intake_data.get("intake_weight_unit") or "Pounds"
		
		patient_data = {
			"doctype": "Patient",
			"first_name": first_name,
			"last_name": last_name,
			"sex": gender_name,
			"dob": dob_value,
			"email": user_email,
			"mobile": intake_data.get("mobile") or user.mobile_no or "",
			"status": "Disabled",  # Set to "Disabled" until staff activates
			"invite_user": 0,  # Don't create user - already exists
			"user_id": user_email  # Link to existing user
		}
		
		# Add height_unit and weight_unit if Patient DocType has these fields
		patient_meta = frappe.get_meta("Patient")
		if patient_meta.get_field("height_unit"):
			patient_data["height_unit"] = height_unit
		if patient_meta.get_field("weight_unit"):
			patient_data["weight_unit"] = weight_unit
		
		patient = frappe.get_doc(patient_data)
		patient.flags.skip_user_creation = True  # Prevent user creation hook
		patient.insert(ignore_permissions=True)
	
	# Create GLP-1 Intake Submission child record by appending to patient
	# Use the actual field names from GLP-1 Intake Submission DocType
	# The intake_data already has the correct field names from the web form
	# We just need to copy all fields that exist in GLP-1 Intake Submission
	
	# Get the meta for GLP-1 Intake Submission to know which fields to copy
	submission_meta = frappe.get_meta("GLP-1 Intake Submission")
	
	# Get all valid field names (exclude layout fields)
	valid_fieldnames = {
		f.fieldname for f in submission_meta.fields 
		if f.fieldtype not in ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button']
	}
	
	# Create child table data by copying all matching fields from intake_data
	intake_submission_data = {}
	for fieldname in valid_fieldnames:
		# Get value from intake_data
		value = intake_data.get(fieldname)
		
		# Include the value if it's not None
		# For empty strings, only include if it's a critical field
		if value is not None:
			if value != "" or fieldname in ["email", "first_name", "last_name", "mobile"]:
				intake_submission_data[fieldname] = value
		# Also handle False for checkboxes (convert to 0)
		elif value is False:
			intake_submission_data[fieldname] = 0
	
	# Ensure required/critical fields are set
	if "email" not in intake_submission_data or not intake_submission_data.get("email"):
		intake_submission_data["email"] = user_email
	if "first_name" not in intake_submission_data and intake_data.get("first_name"):
		intake_submission_data["first_name"] = intake_data.get("first_name")
	if "last_name" not in intake_submission_data and intake_data.get("last_name"):
		intake_submission_data["last_name"] = intake_data.get("last_name")
	
	# Append intake submission to patient's child table
	patient.append("glp1_intake_forms", intake_submission_data)
	
	# Ensure status is "Disabled"
	if patient.status != "Disabled":
		patient.status = "Disabled"
	
	# Save patient with intake form
	# Set ignore_mandatory flag in case Patient has required fields we don't have data for
	patient.flags.ignore_mandatory = True
	patient.save(ignore_permissions=True)
	
	# Reload to get the created intake form name
	patient.reload()
	intake_form_name = patient.glp1_intake_forms[-1].name if patient.glp1_intake_forms else None
	
	# Log for debugging
	frappe.logger().info(f"Created intake form for patient {patient.name}: {intake_form_name}, total forms: {len(patient.glp1_intake_forms)}")
	
	# Generate AI medical summary from intake form data
	try:
		from koraflow_core.api.medical_summary import generate_medical_summary
		
		medical_summary = generate_medical_summary(intake_data, patient_name=patient.name)
		
		if medical_summary:
			# Check if Patient has ai_medical_summary field
			patient_meta = frappe.get_meta("Patient")
			if patient_meta.get_field("ai_medical_summary"):
				patient.ai_medical_summary = medical_summary
				patient.flags.ignore_mandatory = True
				patient.save(ignore_permissions=True)
				frappe.logger().info(f"Generated and saved AI medical summary for patient {patient.name}")
			else:
				frappe.logger().warning(f"Patient doctype does not have ai_medical_summary field. Run patch to add it.")
		else:
			frappe.logger().warning(f"Failed to generate medical summary for patient {patient.name}")
	except Exception as e:
		# Don't fail patient creation if medical summary generation fails
		frappe.log_error(f"Error generating medical summary for patient {patient.name}: {str(e)}", "Medical Summary Generation Error")
	
	frappe.db.commit()
	
	# Set intake_completed = 1 for the user
	user = frappe.get_doc("User", user_email)
	user.db_set("intake_completed", 1)
	
	frappe.db.commit()
	
	return {
		"success": True,
		"patient": patient.name,
		"intake_form": intake_form_name,
		"status": "Under Review",
		"message": _("Your intake form has been submitted successfully. Your profile is under review.")
	}


@frappe.whitelist(allow_guest=True)
def create_patient_from_signup(email, full_name):
	"""Create Patient record when user signs up from signup page"""
	try:
		# Check if Patient already exists
		existing_patient = frappe.db.get_value("Patient", {"email": email}, "name")
		
		if existing_patient:
			return {
				"success": True,
				"patient": existing_patient,
				"message": _("Patient record already exists")
			}
		
		# Parse full name
		name_parts = full_name.strip().split()
		first_name = name_parts[0] if name_parts else full_name
		last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
		
		# Get default gender - use "Other" as default if available
		default_gender = None
		for gender_option in ["Other", "Prefer not to say", "Male", "Female"]:
			if frappe.db.exists("Gender", gender_option):
				default_gender = gender_option
				break
		
		if not default_gender:
			frappe.throw(_("No Gender options found. Please contact administrator."))
		
		# Check for duplicate mobile before creating patient
		if user_doc.mobile_no:
			existing_mobile = frappe.db.get_value(
				"Patient",
				{"mobile": user_doc.mobile_no},
				"name"
			)
			if existing_mobile:
				frappe.throw(
					_("Mobile number {0} is already registered to another patient. Please use a different mobile number or contact support.").format(
						frappe.bold(user_doc.mobile_no)
					),
					title=_("Duplicate Mobile Number")
				)
		
		# Create Patient record
		patient = frappe.get_doc({
			"doctype": "Patient",
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"sex": default_gender,  # Required field - set default
			"status": "Active"
		})
		patient.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
		return {
			"success": True,
			"patient": patient.name,
			"message": _("Patient record created successfully")
		}
	except Exception as e:
		frappe.log_error(f"Error creating patient from signup: {str(e)}")
		return {
			"success": False,
			"message": _("Error creating patient record: {0}").format(str(e))
		}


@frappe.whitelist(allow_guest=True)
def custom_sign_up(email: str, full_name: str, password: str = None, redirect_to: str = None) -> tuple[int, str]:
	"""
	Custom signup handler that:
	1. Creates user with Patient user_type and provided password
	2. Adds Patient role
	3. Creates Patient record
	4. Logs user in
	5. Redirects to intake form
	"""
	if is_signup_disabled():
		frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.enabled:
			return 0, _("Already Registered")
		else:
			return 0, _("Registered but disabled")
	else:
		max_signups_allowed_per_hour = cint(frappe.get_system_settings("max_signups_allowed_per_hour") or 300)
		users_created_past_hour = frappe.db.get_creation_count("User", 60)
		if users_created_past_hour >= max_signups_allowed_per_hour:
			frappe.respond_as_web_page(
				_("Temporarily Disabled"),
				_(
					"Too many users signed up recently, so the registration is disabled. Please try back in an hour"
				),
				http_status_code=429,
			)

		# Create user with Patient user_type instead of Website User
		# Set enabled=0 (disabled) - will be activated after medical review
		# Temporarily override User's after_insert to handle Notification Settings with proper permissions
		from frappe.core.doctype.user.user import User as FrappeUser
		original_after_insert = FrappeUser.after_insert
		
		def safe_after_insert(self):
			"""Override after_insert to create Notification Settings with Administrator permissions"""
			original_user = frappe.session.user
			try:
				frappe.set_user("Administrator")
				frappe.flags.ignore_permissions = True
				# Try direct SQL insert first to bypass all permission checks
				try:
					if not frappe.db.exists("Notification Settings", self.name):
						frappe.db.sql("""
							INSERT INTO `tabNotification Settings` 
							(name, enabled, enable_email_notifications, creation, modified, modified_by, owner, docstatus, user)
							VALUES (%s, 1, 1, NOW(), NOW(), %s, %s, 0, %s)
						""", (self.name, "Administrator", "Administrator", self.name))
						frappe.db.commit()
						frappe.logger().info(f"Notification Settings created via SQL for {self.name}")
				except Exception as sql_e:
					# Fallback to DocType method
					try:
						from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings
						create_notification_settings(self.name)
						frappe.db.commit()
					except Exception as doc_e:
						# Log but don't fail - notification settings are not critical
						frappe.log_error(f"Error creating notification settings for {self.name}: SQL={str(sql_e)}, DocType={str(doc_e)}", "User Creation")
			finally:
				frappe.flags.ignore_permissions = False
				frappe.set_user(original_user)
			# Call other after_insert logic
			frappe.cache.delete_key("users_for_mentions")
			frappe.cache.delete_key("enabled_users")
		
		# Temporarily override the method
		FrappeUser.after_insert = safe_after_insert
		
		# Temporarily set user to Administrator to ensure user creation has proper permissions
		original_user = frappe.session.user
		try:
			frappe.set_user("Administrator")
			# Use provided password or generate one
			user_password = password if password else random_string(10)
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": escape_html(full_name),
					"enabled": 0,  # Disabled until medical review
					"new_password": user_password,  # Use provided password or generated one
					"user_type": "Patient",  # Set to Patient instead of Website User
				}
			)
			user.flags.ignore_permissions = True
			user.flags.ignore_password_policy = True
			# Set flag BEFORE insert to prevent hook from running (we'll create Patient manually)
			user.flags.skip_patient_creation_hook = True
			user.insert()
		finally:
			frappe.set_user(original_user)
			# Restore original method
			FrappeUser.after_insert = original_after_insert
		
		# Add Patient role
		user.add_roles("Patient")
		
		# Assign Module Profile to block Drive module
		# Check if Patient Module Profile exists, create if not
		module_profile_name = "Patient Module Profile"
		if not frappe.db.exists("Module Profile", module_profile_name):
			# Create module profile with Drive blocked
			module_profile = frappe.get_doc({
				"doctype": "Module Profile",
				"module_profile_name": module_profile_name
			})
			# Check if Drive module exists
			if frappe.db.exists("Module Def", {"module_name": "Drive"}):
				module_profile.append("block_modules", {"module": "Drive"})
			module_profile.flags.ignore_permissions = True
			module_profile.insert()
			frappe.db.commit()
		
		# Assign module profile to user
		user.module_profile = module_profile_name
		user.flags.ignore_permissions = True
		user.save()
		
		# Create Patient record after user is created
		try:
			create_patient_for_user(user)
		except Exception as e:
			# Log error but don't fail signup - user can complete intake form later
			frappe.log_error(f"Error creating patient during signup: {str(e)}")
			# Don't raise - allow signup to complete even if Patient creation fails

		# Set redirect to intake form wizard if not already set
		if not redirect_to:
			redirect_to = "/glp1-intake/new"
		
		# Ensure we commit any pending database changes
		frappe.db.commit()
		
		# Log the user in directly using LoginManager
		# This bypasses the need for a token and ensures proper session setup
		from frappe.auth import LoginManager
		login_manager = LoginManager()
		login_manager.authenticate(user=user.name, pwd=user_password)
		login_manager.post_login()
		
		# Return success with redirect URL
		# Format: (status_code, message, redirect_url)
		# Status 3 = Success with redirect and auto-login
		try:
			return 3, _("Account created successfully. Redirecting to intake form..."), redirect_to
		except Exception as e:
			# If return fails for some reason, log and return basic success
			frappe.log_error(f"Error returning signup response: {str(e)}", "Signup Response")
			return 2, _("Account created successfully. Please log in to continue."), redirect_to


def create_patient_for_user(user_doc):
	"""Create Patient record for a new user signup"""
	try:
		# Parse name
		first_name = user_doc.first_name or ""
		last_name = user_doc.last_name or ""
		
		# Check if Patient already exists
		existing_patient = frappe.db.get_value("Patient", {"email": user_doc.email}, "name")
		if existing_patient:
			# Link user to existing patient
			frappe.db.set_value("Patient", existing_patient, "user_id", user_doc.name)
			return existing_patient
		
		# Get default gender - use "Other" as default if available, otherwise try "Prefer not to say"
		default_gender = None
		for gender_option in ["Other", "Prefer not to say", "Male", "Female"]:
			if frappe.db.exists("Gender", gender_option):
				default_gender = gender_option
				break
		
		if not default_gender:
			# If no gender options exist, this will fail, but we'll let it fail with a clear error
			frappe.throw(_("No Gender options found. Please contact administrator."))
		
		# Check for duplicate mobile before creating patient
		if user_doc.mobile_no:
			existing_mobile = frappe.db.get_value(
				"Patient",
				{"mobile": user_doc.mobile_no},
				"name"
			)
			if existing_mobile:
				frappe.throw(
					_("Mobile number {0} is already registered to another patient. Please use a different mobile number or contact support.").format(
						frappe.bold(user_doc.mobile_no)
					),
					title=_("Duplicate Mobile Number")
				)
		
		# Create Patient record
		# Set invite_user = 0 to prevent Patient from trying to create a User
		# Set user_id immediately since User already exists
		patient = frappe.get_doc({
			"doctype": "Patient",
			"first_name": first_name,
			"last_name": last_name,
			"email": user_doc.email,
			"mobile": user_doc.mobile_no or "",
			"sex": default_gender,  # Required field - set default
			"status": "Active",
			"invite_user": 0,  # Disable user creation - User already exists
			"user_id": user_doc.name  # Link to existing User
		})
		patient.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
		return patient.name
	except Exception as e:
		frappe.log_error(f"Error creating patient for user {user_doc.email}: {str(e)}")
		raise


@frappe.whitelist()
def process_intake_submission_from_web_form(doc, user_email=None, original_data=None):
	"""Process intake form submission from web form - appends to Patient's child table
	
	Args:
		doc: Document object from web form (may not have all values accessible for child table DocTypes)
		user_email: Email of the user submitting the form
		original_data: Original data dict from web form submission (has all field values)
	"""
	try:
		frappe.logger().info(f"[process_intake_submission_from_web_form] Called with user_email={user_email}, session_user={frappe.session.user}")
		frappe.logger().info(f"[process_intake_submission_from_web_form] Doc type: {type(doc)}")
		frappe.logger().info(f"[process_intake_submission_from_web_form] Has original_data: {original_data is not None}")
		
		if not user_email:
			user_email = frappe.session.user if frappe.session.user != "Guest" else (getattr(doc, 'email', None) or doc.get('email'))
		
		frappe.logger().info(f"[process_intake_submission_from_web_form] Using user_email={user_email}")
		
		if not user_email or user_email == "Guest":
			frappe.logger().error(f"[process_intake_submission_from_web_form] No valid user_email found")
			frappe.throw(_("You must be logged in to submit this form"))
		
		# Convert doc to dict for easier access
		try:
			if hasattr(doc, 'as_dict'):
				doc_dict = doc.as_dict()
				frappe.logger().info(f"[process_intake_submission_from_web_form] Doc converted to dict, keys: {list(doc_dict.keys())[:10]}")
			else:
				doc_dict = dict(doc) if hasattr(doc, '__iter__') and not isinstance(doc, str) else {}
				frappe.logger().info(f"[process_intake_submission_from_web_form] Doc converted to dict (fallback), keys: {list(doc_dict.keys())[:10] if doc_dict else 'empty'}")
		except Exception as e:
			frappe.logger().error(f"[process_intake_submission_from_web_form] Error converting doc to dict: {str(e)}")
			doc_dict = {}
		
		# Helper function to get value from doc
		def get_doc_value(fieldname):
			try:
				if hasattr(doc, 'get'):
					value = doc.get(fieldname)
					if value is not None:
						return value
				if hasattr(doc, fieldname):
					value = getattr(doc, fieldname, None)
					if value is not None:
						return value
				return doc_dict.get(fieldname)
			except Exception as e:
				frappe.logger().warning(f"[process_intake_submission_from_web_form] Error getting field {fieldname}: {str(e)}")
				return None
		
		# Validate uniqueness before processing
		# Check for duplicate ID Number (check across all child table entries)
		if get_doc_value("id_number__passport_number"):
			id_number = get_doc_value("id_number__passport_number")
			existing_id = frappe.db.sql("""
				SELECT name
				FROM `tabGLP-1 Intake Submission`
				WHERE id_number__passport_number = %s
				LIMIT 1
			""", (id_number,), as_dict=True)
			
			if existing_id:
				frappe.throw(
					_("ID Number / Passport Number {0} is already registered. Please use a different ID Number.").format(
						frappe.bold(id_number)
					),
					title=_("Duplicate ID Number")
				)
		
		# Check for duplicate Mobile
		doc_mobile = get_doc_value('mobile')
		if doc_mobile:
			# Check in intake submissions (child table)
			existing_mobile_intake = frappe.db.sql("""
				SELECT name
				FROM `tabGLP-1 Intake Submission`
				WHERE mobile = %s
				LIMIT 1
			""", (doc_mobile,), as_dict=True)
			
			if existing_mobile_intake:
				frappe.throw(
					_("Mobile number {0} is already registered. Please use a different mobile number.").format(
						frappe.bold(doc_mobile)
					),
					title=_("Duplicate Mobile Number")
				)
			
			# Check in Patient records
			existing_mobile_patient = frappe.db.get_value(
				"Patient",
				{"mobile": doc_mobile},
				"name"
			)
			if existing_mobile_patient:
				frappe.throw(
					_("Mobile number {0} is already registered to another patient. Please use a different mobile number.").format(
						frappe.bold(doc_mobile)
					),
					title=_("Duplicate Mobile Number")
				)
		
		# Get or create patient
		patient = frappe.db.get_value("Patient", {"email": user_email}, "name")
		if not patient:
			# Create patient first
			user = frappe.get_doc("User", user_email)
			
			# Check for duplicate mobile when creating patient
			patient_mobile = doc_mobile or user.mobile_no or ""
			if patient_mobile:
				existing_patient_mobile = frappe.db.get_value(
					"Patient",
					{"mobile": patient_mobile},
					"name"
				)
				if existing_patient_mobile:
					frappe.throw(
						_("Mobile number {0} is already registered to another patient. Please use a different mobile number.").format(
							frappe.bold(patient_mobile)
						),
						title=_("Duplicate Mobile Number")
					)
			
			# Handle sex/gender field - can be from sex (Link) or biological_sex (Select) or gender
			sex_value = get_doc_value('sex') or get_doc_value('biological_sex') or get_doc_value('gender')
			if isinstance(sex_value, str):
				# If it's a string, try to get the Gender record
				gender_name = frappe.db.get_value("Gender", {"name": sex_value}, "name") or sex_value
			else:
				gender_name = "Male"  # Default
			
			patient_doc = frappe.get_doc({
				"doctype": "Patient",
				"first_name": get_doc_value('first_name') or user.first_name,
				"last_name": get_doc_value('last_name') or user.last_name or "",
				"sex": gender_name,
				"dob": get_doc_value('dob') or get_doc_value('date_of_birth'),
				"email": user_email,
				"mobile": patient_mobile,
				"status": "Disabled",
				"invite_user": 0,
				"user_id": user_email
			})
			patient_doc.flags.skip_user_creation = True
			patient_doc.insert(ignore_permissions=True)
			patient = patient_doc  # Keep as Document object, not just name
		else:
			patient = frappe.get_doc("Patient", patient)
			if patient.status == "Active":
				patient.status = "Disabled"
			if not patient.user_id:
				patient.user_id = user_email
			patient.flags.skip_user_creation = True
		
		# Copy all fields from doc to child table entry
		# The doc object should have all values set via doc.set() in web_form.accept()
		# CRITICAL: For child table DocTypes, doc.get() should work for values set via doc.set()
		
		# First, verify doc has values
		frappe.logger().info(f"[process_intake_submission_from_web_form] VERIFICATION - doc.get('email') = {doc.get('email') if hasattr(doc, 'get') else 'N/A'}")
		frappe.logger().info(f"[process_intake_submission_from_web_form] VERIFICATION - doc.get('first_name') = {doc.get('first_name') if hasattr(doc, 'get') else 'N/A'}")
		frappe.logger().info(f"[process_intake_submission_from_web_form] VERIFICATION - doc.get('last_name') = {doc.get('last_name') if hasattr(doc, 'get') else 'N/A'}")
		
		# Convert doc to dict if it's a Document instance
		if hasattr(doc, 'as_dict'):
			doc_dict = doc.as_dict()
			frappe.logger().info(f"[process_intake_submission_from_web_form] Doc as_dict has {len(doc_dict)} keys")
			# Log key values from as_dict
			for key in ['email', 'first_name', 'last_name', 'mobile']:
				if key in doc_dict:
					frappe.logger().info(f"[process_intake_submission_from_web_form] doc_dict['{key}'] = {doc_dict[key]}")
		else:
			doc_dict = dict(doc) if hasattr(doc, '__iter__') and not isinstance(doc, str) else {}
			frappe.logger().info(f"[process_intake_submission_from_web_form] Doc dict has {len(doc_dict)} keys")
		
		# Build submission_data directly from doc using doc.get() - this is the most reliable
		
		# Get the meta for GLP-1 Intake Submission to know which fields to copy
		submission_meta = frappe.get_meta("GLP-1 Intake Submission")
		valid_fieldnames = {
			f.fieldname for f in submission_meta.fields 
			if f.fieldtype not in ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button']
		}
		
		frappe.logger().info(f"[process_intake_submission_from_web_form] Valid fieldnames to copy: {len(valid_fieldnames)} fields")
		
		# Copy ALL fields - prioritize original_data if available (most reliable source)
		# For child table DocTypes, the doc object might not have values accessible
		submission_data = {}
		
		# First, try to get values from original_data (the form submission data)
		# This is the most reliable source since it has all the form values
		if original_data:
			frappe.logger().info(f"[process_intake_submission_from_web_form] Using original_data")
			# Handle both dict and frappe._dict
			if isinstance(original_data, dict):
				data_source = original_data
			elif hasattr(original_data, '__dict__'):
				data_source = dict(original_data)
			else:
				data_source = {}
			
			frappe.logger().info(f"[process_intake_submission_from_web_form] original_data has {len(data_source)} keys: {list(data_source.keys())[:15]}")
			
			for fieldname in valid_fieldnames:
				if fieldname in data_source:
					value = data_source[fieldname]
					# Include the value if it's not None (include empty strings for important fields)
					if value is not None:
						submission_data[fieldname] = value
					elif value is False:
						submission_data[fieldname] = 0
					elif fieldname in ["email", "first_name", "last_name", "mobile"] and value == "":
						submission_data[fieldname] = value
		
		# Then, supplement with values from doc (in case original_data is missing some)
		for fieldname in valid_fieldnames:
			if fieldname not in submission_data:  # Only if not already set from original_data
				# Use doc.get() directly - this is the most reliable method
				if hasattr(doc, 'get'):
					value = doc.get(fieldname)
				elif hasattr(doc, fieldname):
					value = getattr(doc, fieldname, None)
				elif fieldname in doc_dict:
					value = doc_dict.get(fieldname)
				else:
					value = None
				
				# Include the value if it exists
				if value is not None:
					submission_data[fieldname] = value
				elif value is False:
					submission_data[fieldname] = 0
		
		# Ensure email is ALWAYS set (override with user_email from session)
		submission_data['email'] = user_email
		
		# Ensure first_name is set if we have it from user
		if 'first_name' not in submission_data or not submission_data.get('first_name'):
			user_doc = frappe.get_doc("User", user_email)
			if user_doc.first_name:
				submission_data['first_name'] = user_doc.first_name
		
		# Note: form_status might not exist in the DocType, so don't set it here
		# It will be set via the DocType's on_insert or other hooks if needed
		# submission_data['form_status'] = "Under Review"  # Removed - field doesn't exist
		
		frappe.logger().info(f"[process_intake_submission_from_web_form] Final submission_data has {len(submission_data)} fields")
		frappe.logger().info(f"[process_intake_submission_from_web_form] Key fields - Email: {submission_data.get('email')}, First name: {submission_data.get('first_name')}, Last name: {submission_data.get('last_name')}, Mobile: {submission_data.get('mobile')}")
		frappe.logger().info(f"[process_intake_submission_from_web_form] Sample of submission_data keys: {list(submission_data.keys())[:20]}")
		
		# Log submission_data before inserting
		print(f"[process_intake_submission_from_web_form] About to insert submission_data with {len(submission_data)} fields")
		print(f"[process_intake_submission_from_web_form] submission_data keys: {list(submission_data.keys())[:20]}")
		for key in ['email', 'first_name', 'last_name', 'mobile', 'dob', 'sex', 'intake_height_unit', 'intake_height_cm']:
			if key in submission_data:
				print(f"[process_intake_submission_from_web_form] submission_data['{key}'] = {submission_data[key]}")
		
		frappe.logger().info(f"[process_intake_submission_from_web_form] About to insert submission_data with {len(submission_data)} fields")
		frappe.logger().info(f"[process_intake_submission_from_web_form] submission_data keys: {list(submission_data.keys())[:20]}")
		
		# CRITICAL: Insert child table row directly using SQL to bypass permission checks
		# The issue is that Frappe's get_valid_dict() filters fields based on permitted_fieldnames
		# For child table DocTypes, email/first_name/last_name aren't in permitted_fieldnames
		# So we need to insert directly using SQL
		
		# Get the next idx for the child table
		existing_count = frappe.db.sql("""
			SELECT COUNT(*) as cnt 
			FROM `tabGLP-1 Intake Submission`
			WHERE parent = %s AND parentfield = 'glp1_intake_forms'
		""", (patient.name,), as_dict=True)
		next_idx = (existing_count[0]['cnt'] if existing_count else 0) + 1
		
		# Build insert dict with all required fields
		# Note: 'doctype' is not a database column, so don't include it
		# Generate a name for the child table row (Frappe uses hash-based naming)
		from frappe.model.naming import make_autoname
		child_name = frappe.generate_hash(length=10)
		
		insert_dict = {
			"name": child_name,
			"parent": patient.name,
			"parenttype": "Patient",
			"parentfield": "glp1_intake_forms",
			"idx": next_idx,
		}
		
		# Add all submission_data fields that are in valid_fieldnames
		# Filter out empty strings and None values, and handle field types properly
		meta = frappe.get_meta("GLP-1 Intake Submission")
		for key, value in submission_data.items():
			if key not in valid_fieldnames:
				continue
			
			# Skip None and empty strings for all field types (let database use defaults)
			if value is None or value == "":
				continue
			
			# Handle numeric fields - ensure they're proper types
			field = meta.get_field(key)
			if field:
				if field.fieldtype in ["Int", "Float", "Currency", "Percent"]:
					try:
						if field.fieldtype == "Int":
							value = int(value)
						else:
							value = float(value)
					except (ValueError, TypeError):
						continue  # Skip invalid numeric values
				elif field.fieldtype == "Date" and value == "":
					continue  # Skip empty dates
				elif field.fieldtype == "Check":
					value = 1 if value else 0
			
			insert_dict[key] = value
		
		# Insert directly using SQL (exclude 'doctype' as it's not a column)
		columns = [c for c in insert_dict.keys() if c != "doctype"]
		values = [insert_dict[c] for c in columns]
		
		intake_form_name = None
		try:
			print(f"[process_intake_submission_from_web_form] Attempting direct SQL insert with {len(columns)} columns")
			frappe.db.sql(
				f"""INSERT INTO `tabGLP-1 Intake Submission` ({', '.join(f'`{c}`' for c in columns)})
					VALUES ({', '.join(['%s'] * len(values))})""",
				values
			)
			frappe.db.commit()
			print(f"[process_intake_submission_from_web_form] SQL insert executed successfully")
			
			# Get the inserted row name
			intake_form_name = frappe.db.get_value(
				"GLP-1 Intake Submission",
				{"parent": patient.name, "parentfield": "glp1_intake_forms"},
				"name",
				order_by="creation DESC"
			)
			
			frappe.logger().info(f"[process_intake_submission_from_web_form] Directly inserted intake form: {intake_form_name} with {len(insert_dict)} fields")
			print(f"[process_intake_submission_from_web_form] Directly inserted intake form: {intake_form_name}")
			
			# Verify the insert worked
			db_email = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "email")
			db_first_name = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "first_name")
			frappe.logger().info(f"[process_intake_submission_from_web_form] After direct insert - email: {db_email}, first_name: {db_first_name}")
			print(f"[process_intake_submission_from_web_form] After direct insert - email: {db_email}, first_name: {db_first_name}")
			
			# Reload patient to refresh child table
			patient.reload()
			
		except Exception as e:
			frappe.logger().error(f"[process_intake_submission_from_web_form] Error in direct SQL insert: {str(e)}")
			import traceback
			error_traceback = traceback.format_exc()
			frappe.logger().error(f"[process_intake_submission_from_web_form] Traceback: {error_traceback}")
			print(f"[process_intake_submission_from_web_form] Error in direct SQL insert: {str(e)}")
			print(f"[process_intake_submission_from_web_form] Traceback: {error_traceback[:500]}")
			frappe.db.rollback()
			# Fall back to append + save method
			patient.append("glp1_intake_forms", submission_data)
			patient.flags.ignore_mandatory = True
			patient.save(ignore_permissions=True)
			patient.reload()
			intake_form_name = patient.glp1_intake_forms[-1].name if patient.glp1_intake_forms else None
		
		# Get the created intake form name (should already be set from direct insert)
		if not intake_form_name:
			patient.reload()
			intake_form_name = patient.glp1_intake_forms[-1].name if patient.glp1_intake_forms else None
		
		# Verify fields were saved (should be if direct insert worked)
		if intake_form_name:
			db_email = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "email")
			db_first_name = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "first_name")
			if not db_email or not db_first_name:
				# Fields weren't saved, update them directly as fallback
				update_fields = {}
				for key, value in submission_data.items():
					if value is not None and key in valid_fieldnames:
						update_fields[key] = value
				
				if update_fields:
					frappe.db.set_value("GLP-1 Intake Submission", intake_form_name, update_fields, update_modified=False)
					frappe.db.commit()
					frappe.logger().info(f"[process_intake_submission_from_web_form] Updated {len(update_fields)} fields directly in database for {intake_form_name}")
					
					# Verify the update worked
					db_email = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "email")
					db_first_name = frappe.db.get_value("GLP-1 Intake Submission", intake_form_name, "first_name")
					print(f"[process_intake_submission_from_web_form] After DB update - email: {db_email}, first_name: {db_first_name}")
		
		# Generate AI medical summary from intake form data
		try:
			from koraflow_core.api.medical_summary import generate_medical_summary
			
			# Convert submission_data to intake_data format for medical summary
			intake_data_for_summary = submission_data.copy()
			intake_data_for_summary['email'] = user_email
			
			frappe.logger().info(f"[process_intake_submission_from_web_form] Generating medical summary for patient {patient.name}")
			medical_summary = generate_medical_summary(intake_data_for_summary, patient_name=patient.name)
			
			if medical_summary:
				frappe.logger().info(f"[process_intake_submission_from_web_form] Medical summary generated successfully ({len(medical_summary)} chars)")
				# Check if Patient has ai_medical_summary field
				patient_meta = frappe.get_meta("Patient")
				if patient_meta.get_field("ai_medical_summary"):
					patient.ai_medical_summary = medical_summary
					patient.flags.ignore_mandatory = True
					patient.save(ignore_permissions=True)
					frappe.logger().info(f"Generated and saved AI medical summary for patient {patient.name}")
				else:
					frappe.logger().warning(f"Patient doctype does not have ai_medical_summary field. Run patch to add it.")
			else:
				frappe.logger().warning(f"Failed to generate medical summary for patient {patient.name}")
		except Exception as e:
			# Don't fail intake submission if medical summary generation fails
			frappe.log_error(f"Error generating medical summary for patient {patient.name}: {str(e)}", "Medical Summary Generation Error")
		
		# Set intake_completed = 1 for the user
		frappe.logger().info(f"[process_intake_submission_from_web_form] Setting intake_completed=1 for user {user_email}")
		user = frappe.get_doc("User", user_email)
		user.db_set("intake_completed", 1)
		frappe.logger().info(f"[process_intake_submission_from_web_form] Successfully set intake_completed=1 for user {user_email}")
		
		# Enable the user if they were disabled (they should be able to access the system after form submission)
		if not user.enabled:
			user.enabled = 1
			user.flags.ignore_permissions = True
			user.save()
			frappe.logger().info(f"[process_intake_submission_from_web_form] Enabled user {user_email} after intake form submission")
		
		frappe.db.commit()
		
		return {
			"success": True,
			"patient": patient.name,
			"intake_form_name": intake_form_name,
			"status": "Under Review",
			"message": _("Your intake form has been submitted. Your profile is under review. You will receive an email once your profile is activated by our medical staff.")
		}
	except Exception as e:
		import traceback
		error_traceback = traceback.format_exc()
		frappe.log_error(f"Error processing intake form submission: {str(e)}\n\nTraceback:\n{error_traceback}", "GLP-1 Intake Submission Error")
		frappe.logger().error(f"[process_intake_submission_from_web_form] Exception: {str(e)}")
		frappe.logger().error(f"[process_intake_submission_from_web_form] Traceback: {error_traceback}")
		# Re-raise the exception so it can be caught by the web form handler
		raise


@frappe.whitelist()
def process_intake_submission(doc, method=None):
	"""Process intake form submission after insert - called via doc_events hook"""
	from koraflow_core.api.patient_signup import create_patient_from_intake
	
	# Get user email - prioritize logged-in user over form email
	if frappe.session.user and frappe.session.user != "Guest":
		user_email = frappe.session.user
	else:
		user_email = doc.email
	
	frappe.logger().info(f"[process_intake_submission] Processing submission {doc.name} for {user_email}")
	
	if not user_email or user_email == "Guest":
		frappe.log_error("No user email found for intake form submission", "GLP-1 Intake Submission Error")
		return
	
	# Convert submission data to intake_data format
	intake_data = doc.as_dict()
	
	# Ensure email is set in intake_data
	if not intake_data.get('email'):
		intake_data['email'] = user_email
	
	try:
		# Create patient and intake form child record
		result = create_patient_from_intake(intake_data, user_email=user_email)
		
		if result and result.get('success'):
			frappe.logger().info(f"Intake form submitted for {user_email}, patient: {result.get('patient')}, intake_form: {result.get('intake_form')}")
			frappe.db.commit()
		else:
			error_msg = result.get('message') if isinstance(result, dict) else str(result)
			frappe.log_error(f"Failed to create patient from intake: {error_msg}", "GLP-1 Intake Submission Error")
	except Exception as e:
		import traceback
		error_traceback = traceback.format_exc()
		frappe.log_error(f"Error processing intake form submission: {str(e)}\n\nTraceback:\n{error_traceback}", "GLP-1 Intake Submission Error")
		frappe.logger().error(f"[process_intake_submission_from_web_form] Exception: {str(e)}")
		frappe.logger().error(f"[process_intake_submission_from_web_form] Traceback: {error_traceback}")
		# Re-raise the exception so it can be caught by the web form handler
		raise


@frappe.whitelist(allow_guest=True)
def patient_sign_up(email: str, full_name: str, redirect_to: str = None) -> tuple[int, str]:
	"""
	Patient signup handler that:
	1. Creates user with Website User/Patient user_type
	2. Sets email_verified = 0
	3. Generates verification token
	4. Sends verification email
	5. Does NOT collect password at signup
	"""
	# #region agent log
	import json, os
	log_path = "/Users/tjaartprinsloo/Documents/KoraFlow/.cursor/debug.log"
	try:
		with open(log_path, "a") as f:
			f.write(json.dumps({"id":"log_patient_1","timestamp":int(__import__("time").time()*1000),"location":"patient_signup.py:patient_sign_up","message":"Function called","data":{"email":email[:10]+"..." if email else None,"full_name":full_name[:20] if full_name else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+"\n")
	except: pass
	# #endregion
	
	if is_signup_disabled():
		frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.enabled:
			return 0, _("Already Registered")
		else:
			return 0, _("Registered but disabled")
	else:
		max_signups_allowed_per_hour = cint(frappe.get_system_settings("max_signups_allowed_per_hour") or 300)
		users_created_past_hour = frappe.db.get_creation_count("User", 60)
		if users_created_past_hour >= max_signups_allowed_per_hour:
			frappe.respond_as_web_page(
				_("Temporarily Disabled"),
				_(
					"Too many users signed up recently, so the registration is disabled. Please try back in an hour"
				),
				http_status_code=429,
			)

		# Generate verification token (can be done as Guest)
		verification_key = frappe.generate_hash()
		hashed_key = sha256_hash(verification_key)
		
		# Create user with Administrator context
		# CRITICAL: User.after_insert() calls create_notification_settings() which requires Administrator context
		# We need to override after_insert to ensure it runs with Administrator permissions
		from frappe.core.doctype.user.user import User as FrappeUser
		original_after_insert = FrappeUser.after_insert
		
		def safe_after_insert(self):
			"""Override after_insert to ensure Notification Settings creation uses Administrator context"""
			original_user = frappe.session.user
			try:
				frappe.set_user("Administrator")
				frappe.flags.ignore_permissions = True
				# Call original after_insert which creates Notification Settings
				original_after_insert(self)
			finally:
				frappe.flags.ignore_permissions = False
				frappe.set_user(original_user)
		
		# Temporarily override the method
		FrappeUser.after_insert = safe_after_insert
		
		original_user = frappe.session.user
		try:
			# Create user with Administrator context
			frappe.set_user("Administrator")
			frappe.flags.ignore_permissions = True
			# Use System User type if Website User doesn't exist
			# Get default user type from existing users
			default_user_type = frappe.db.get_value("User", {"user_type": ["!=", ""]}, "user_type") or "System User"
			
			# Always use "Patient" role for patient signups
			patient_role = "Patient"
			
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": escape_html(full_name),
					"enabled": 1,
					"user_type": default_user_type,  # Use existing user type
					"roles": [{"role": patient_role}]  # Add Patient role directly in doc creation
				}
			)
			user.flags.ignore_permissions = True
			user.flags.ignore_password_policy = True
			user.flags.no_welcome_mail = True  # Don't send welcome email yet
			
			user.insert()
		finally:
			# Restore original method
			FrappeUser.after_insert = original_after_insert
			frappe.flags.ignore_permissions = False
			frappe.set_user(original_user)
		
		# Continue with Administrator context for remaining operations
		original_user_2 = frappe.session.user
		try:
			frappe.set_user("Administrator")
			frappe.flags.ignore_permissions = True
			
			# Reload user to ensure we have the latest state
			user.reload()
			
			# IMMEDIATELY assign Patient role - ensure it's there
			patient_role = "Patient"
			user_roles = [r.role for r in user.roles]
			# #region agent log
			try:
				with open(log_path, "a") as f:
					f.write(json.dumps({"id":"log_patient_2","timestamp":int(__import__("time").time()*1000),"location":"patient_signup.py:patient_sign_up","message":"Before role assignment","data":{"user":user.name,"current_roles":user_roles,"patient_role_exists":patient_role in user_roles},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+"\n")
			except: pass
			# #endregion
			
			if patient_role not in user_roles:
				user.add_roles(patient_role)
				user.save(ignore_permissions=True)
				frappe.db.commit()
				# #region agent log
				try:
					with open(log_path, "a") as f:
						f.write(json.dumps({"id":"log_patient_3","timestamp":int(__import__("time").time()*1000),"location":"patient_signup.py:patient_sign_up","message":"Role added via add_roles","data":{"user":user.name},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+"\n")
				except: pass
				# #endregion
			
			# Verify Patient role is assigned (double-check)
			user.reload()
			user_roles_after = [r.role for r in user.roles]
			# #region agent log
			try:
				with open(log_path, "a") as f:
					f.write(json.dumps({"id":"log_patient_4","timestamp":int(__import__("time").time()*1000),"location":"patient_signup.py:patient_sign_up","message":"After role assignment check","data":{"user":user.name,"roles_after":user_roles_after,"patient_role_exists":patient_role in user_roles_after},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+"\n")
			except: pass
			# #endregion
			
			if patient_role not in user_roles_after:
				# Force add role via direct database update if needed
				frappe.db.sql("""
					INSERT INTO `tabHas Role` (name, role, parent, parenttype, parentfield)
					VALUES (%s, %s, %s, 'User', 'roles')
					ON DUPLICATE KEY UPDATE role=role
				""", (frappe.generate_hash(length=10), patient_role, user.name))
				frappe.db.commit()
				user.reload()
				# #region agent log
				try:
					with open(log_path, "a") as f:
						f.write(json.dumps({"id":"log_patient_5","timestamp":int(__import__("time").time()*1000),"location":"patient_signup.py:patient_sign_up","message":"Role added via SQL","data":{"user":user.name},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+"\n")
				except: pass
				# #endregion
			
			# Set email_verified = 0 and store verification token
			user.db_set("email_verified", 0)
			user.db_set("email_verification_key", hashed_key)
			user.db_set("email_verification_key_generated_on", now_datetime())
			
			# Set intake_completed = 0
			user.db_set("intake_completed", 0)
			
			# Generate temporary password for immediate login
			temp_password = random_string(12)
			update_password(user.name, temp_password, logout_all_sessions=False)
			
			# Ensure we commit any pending database changes
			frappe.db.commit()
			
			# Set redirect to intake wizard
			if not redirect_to:
				redirect_to = "/glp1-intake/new"
			frappe.cache.hset("redirect_after_login", user.name, redirect_to)
			
			# Generate login token for auto-login
			# Store credentials in cache for 5 minutes
			import time
			login_token = random_string(32)
			login_data = {
				"user": user.name,
				"password": temp_password,
				"expires": time.time() + 300  # 5 minutes
			}
			frappe.cache.set_value(f"signup_auto_login:{login_token}", login_data, expires_in_sec=300)
			
			# Send verification email (frappe.sendmail() needs Administrator context)
			# But don't block the redirect - user can verify email later
			try:
				verification_url = get_url(f"/verify-email?token={verification_key}&email={email}")
				send_verification_email(user, verification_url)
			except Exception as e:
				# Log the error but don't fail signup - user can verify email later
				error_msg = str(e)
				frappe.log_error(f"Error sending verification email: {error_msg}", "Email Verification Error")
			
			frappe.db.commit()
			
			# Return status 3 to indicate success with immediate redirect to intake form
			# Status 3 = Success with redirect and auto-login
			# Return format: (status, message, redirect_url, login_token)
			return 3, _("Account created successfully. Redirecting to intake form..."), redirect_to, login_token
		finally:
			frappe.flags.ignore_permissions = False
			frappe.set_user(original_user_2)


@frappe.whitelist(allow_guest=True)
def verify_email(token: str, email: str = None):
	"""
	Verify email using token from verification email.
	Sets email_verified = 1 and triggers password setup email.
	"""
	if not token:
		frappe.respond_as_web_page(
			_("Invalid Link"),
			_("Verification link is invalid or expired."),
			http_status_code=400,
		)
		return
	
	hashed_token = sha256_hash(token)
	
	# Find user by token (read-only operations, Guest OK)
	if email:
		user_dict = frappe.db.get("User", {"email": email}, ["name", "email_verified", "email_verification_key"])
		if not user_dict:
			frappe.respond_as_web_page(
				_("Invalid Link"),
				_("Verification link is invalid or expired."),
				http_status_code=400,
			)
			return
		user_name = user_dict.name
		user_verification_key = user_dict.get("email_verification_key")
		email_verified = user_dict.get("email_verified", 0)
	else:
		# Search by token
		users = frappe.db.sql("""
			SELECT name, email_verified, email_verification_key FROM `tabUser`
			WHERE email_verification_key = %s
			AND email_verified = 0
		""", (hashed_token,), as_dict=True)
		
		if not users:
			frappe.respond_as_web_page(
				_("Invalid Link"),
				_("Verification link is invalid or expired."),
				http_status_code=400,
			)
			return
		user_name = users[0].name
		user_verification_key = users[0].get("email_verification_key")
		email_verified = users[0].get("email_verified", 0)
	
	# Verify token matches
	if not user_verification_key or user_verification_key != hashed_token:
		frappe.respond_as_web_page(
			_("Invalid Link"),
			_("Verification link is invalid or expired."),
			http_status_code=400,
		)
		return
	
	# Check if already verified
	if email_verified:
		frappe.respond_as_web_page(
			_("Already Verified"),
			_("Your email has already been verified. You can log in or reset your password."),
			indicator_color="green",
		)
		return
	
	# Set email as verified and trigger password setup with Administrator context
	# reset_password() requires Administrator context for Notification Settings access
	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")
		frappe.flags.ignore_permissions = True
		# Get user doc within Administrator context
		user = frappe.get_doc("User", user_name)
		
		user.db_set("email_verified", 1)
		user.db_set("email_verified_on", now_datetime())
		user.db_set("email_verified_via", "Email")
		user.db_set("email_verification_key", None)  # Clear token after use
		
		# Set redirect to intake form after password setup
		frappe.cache.hset("redirect_after_login", user.name, "/glp1-intake")
		
		frappe.db.commit()
		
		# Trigger password setup email (requires Administrator context)
		try:
			user.reset_password(send_email=True)
			frappe.respond_as_web_page(
				_("Email Verified"),
				_("Your email has been verified! Please check your email for password setup instructions."),
				indicator_color="green",
			)
		except Exception as e:
			frappe.log_error(f"Error sending password setup email: {str(e)}", "Password Setup Error")
			frappe.respond_as_web_page(
				_("Email Verified"),
				_("Your email has been verified! However, we couldn't send the password setup email. Please contact support."),
				indicator_color="orange",
			)
	finally:
		frappe.flags.ignore_permissions = False
		frappe.set_user(original_user)


def send_verification_email(user, verification_url):
	"""Send email verification email to user
	Must be called within Administrator context to access Notification Settings
	"""
	subject = _("Verify Your Email - KoraFlow")
	message = f"""
	<p>Dear {user.first_name},</p>
	
	<p>Thank you for signing up with KoraFlow!</p>
	
	<p>Please verify your email address by clicking the link below:</p>
	
	<p style="margin: 30px 0px;">
		<a href="{verification_url}" rel="nofollow" style="padding: 8px 20px; background-color: #7575ff; color: #fff; border-radius: 4px; text-decoration: none; line-height: 1; border-bottom: 3px solid rgba(0, 0, 0, 0.2); font-size: 14px; font-weight: 200;">Verify Email</a>
	</p>
	
	<br>
	<p style="font-size: 85%;">You can also copy-paste this link in your browser: <a href="{verification_url}">{verification_url}</a></p>
	
	<p>After verifying your email, you'll receive a password setup link.</p>
	
	<p>Best regards,<br>The KoraFlow Team</p>
	"""
	
	# frappe.sendmail() internally accesses Notification Settings
	# Must be called within Administrator context
	frappe.sendmail(
		recipients=[user.email],
		subject=subject,
		message=message,
		now=True
	)


@frappe.whitelist()
def force_verify_email(user_email: str, reason: str = None):
	"""
	Admin function to force verify email for assisted patients.
	Sets email_verified = 1 and triggers password setup email.
	"""
	# Check permissions - only admins/staff can force verify
	if not frappe.has_permission("User", "write"):
		frappe.throw(_("You do not have permission to verify emails"), frappe.PermissionError)
	
	user = frappe.get_doc("User", user_email)
	
	if user.email_verified:
		frappe.msgprint(_("Email is already verified for this user"))
		return
	
	# Set email as verified via admin and trigger password setup
	# reset_password() requires Administrator context for Notification Settings access
	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")
		frappe.flags.ignore_permissions = True
		user.db_set("email_verified", 1)
		user.db_set("email_verified_on", now_datetime())
		user.db_set("email_verified_via", "Admin")
		user.db_set("email_verified_by", original_user)  # Use original user (admin who clicked button)
		if reason:
			frappe.db.set_value("User", user_email, "email_verification_reason", reason)
		
		# Set redirect to intake form after password setup
		frappe.cache.hset("redirect_after_login", user_email, "/glp1-intake")
		
		frappe.db.commit()
		
		# Trigger password setup email (requires Administrator context)
		try:
			user.reset_password(send_email=True)
			frappe.msgprint(_("Email verified and password setup email sent to {0}").format(user_email))
		except Exception as e:
			frappe.log_error(f"Error sending password setup email: {str(e)}", "Password Setup Error")
			frappe.msgprint(_("Email verified, but password setup email could not be sent. Please send manually."), indicator="orange")
	finally:
		frappe.flags.ignore_permissions = False
		frappe.set_user(original_user)


@frappe.whitelist()
def activate_patient_profile(patient_name):
	"""
	Activate a patient profile after medical staff review.
	This will:
	1. Set patient status to "Active"
	2. Generate a temporary password
	3. Send email with temporary password
	4. Return the temporary password (for staff reference)
	"""
	# Check permissions - only staff with appropriate roles should be able to activate
	if not frappe.has_permission("Patient", "write"):
		frappe.throw(_("You do not have permission to activate patient profiles"), frappe.PermissionError)
	
	# Get patient record
	patient = frappe.get_doc("Patient", patient_name)
	
	if patient.status == "Active":
		frappe.throw(_("Patient profile is already active"))
	
	# Get user associated with patient
	if not patient.user_id:
		frappe.throw(_("No user account found for this patient. Please link a user first."))
	
	user = frappe.get_doc("User", patient.user_id)
	
	# Generate temporary password
	temp_password = random_string(12)
	
	# Update user password
	update_password(user.name, temp_password, logout_all_sessions=True)
	
	# Update patient status to Active
	patient.status = "Active"
	patient.save(ignore_permissions=True)
	
	frappe.db.commit()
	
	# Send email with temporary password
	try:
		subject = _("Your KoraFlow Account is Ready")
		message = f"""
		<p>Dear {user.first_name},</p>
		
		<p>Your patient profile has been reviewed and activated by our medical staff.</p>
		
		<p>You can now log in to your account using the following credentials:</p>
		<ul>
			<li><strong>Email:</strong> {user.email}</li>
			<li><strong>Temporary Password:</strong> {temp_password}</li>
		</ul>
		
		<p>Please log in at: <a href="{frappe.utils.get_url('/login')}">{frappe.utils.get_url('/login')}</a></p>
		
		<p><strong>Important:</strong> For security reasons, please change your password after your first login.</p>
		
		<p>Best regards,<br>The KoraFlow Team</p>
		"""
		
		frappe.sendmail(
			recipients=[user.email],
			subject=subject,
			message=message,
			now=True
		)
	except Exception as e:
		frappe.log_error(f"Error sending activation email to {user.email}: {str(e)}")
		# Don't fail the activation if email fails - staff can manually provide password
	
	return {
		"success": True,
		"patient": patient.name,
		"user": user.email,
		"temporary_password": temp_password,
		"message": f"Patient profile activated. Temporary password sent to {user.email}"
	}
