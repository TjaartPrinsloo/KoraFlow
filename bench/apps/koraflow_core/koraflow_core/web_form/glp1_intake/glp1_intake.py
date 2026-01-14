import frappe
from frappe import _


def get_context(context):
	"""Get context for the intake form page"""
	context.no_cache = 1
	
	# Check if user is logged in
	# Allow disabled Patient users to access intake form (they need to fill it)
	if frappe.session.user == "Guest":
		# Check if there's a signup token in the URL for auto-login
		import frappe.request
		signup_token = frappe.request.args.get('signup_token') or frappe.form_dict.get('signup_token')
		
		if signup_token:
			# Try to auto-login with the token
			try:
				from koraflow_core.api.auto_login import auto_login_with_token
				login_result = auto_login_with_token(signup_token)
				if login_result.get('success'):
					# User is now logged in, reload the page
					frappe.local.response["type"] = "redirect"
					frappe.local.response["location"] = "/glp1-intake"
					return
			except Exception as e:
				frappe.log_error(f"Error in auto-login from intake form: {str(e)}")
		
		# No token or auto-login failed, show error
		frappe.throw(_("Please login to access this form"), frappe.PermissionError)
	
	# Allow disabled Patient users to access intake form
	# This is the only page they can access when disabled
	if frappe.session.user != "Guest":
		user = frappe.get_doc("User", frappe.session.user)
		if not user.enabled and user.user_type != "Patient":
			# Non-Patient disabled users cannot access
			frappe.throw(_("Your account is disabled. Please contact support."), frappe.PermissionError)
	
	# Check if patient already exists
	user_email = frappe.session.user
	patient_exists = frappe.db.get_value("Patient", {"email": user_email}, "name")
	
	context.patient_exists = bool(patient_exists)
	context.user_email = user_email
	
	# Get intake form status
	from koraflow_core.api.patient_signup import get_intake_form_status
	context.intake_status = get_intake_form_status(user_email)
	
	# Pre-populate email and first_name fields with logged-in user's data
	# Set reference_doc so web form can pre-fill it
	if not hasattr(context, 'reference_doc'):
		context.reference_doc = {}
	
	# Get user's first name
	user = frappe.get_doc("User", user_email)
	first_name = user.first_name or user_email.split('@')[0]  # Fallback to email prefix if no first_name
	
	context.reference_doc['email'] = user_email
	context.reference_doc['first_name'] = first_name
	
	# Add custom script to pre-populate email and first_name fields
	# Since web form is not standard, we need to inject script directly
	populate_script = f"""
	<script>
	frappe.ready(function() {{
		console.log('[GLP1 Intake] Auto-population script loaded');
		console.log('[GLP1 Intake] Session user:', frappe.session ? frappe.session.user : 'No session');
		console.log('[GLP1 Intake] Expected email:', '{user_email}');
		console.log('[GLP1 Intake] Expected first name:', '{first_name}');
		
		// Pre-populate email and first_name fields with logged-in user's data
		function populateFields() {{
			console.log('[GLP1 Intake] populateFields() called');
			
			if (frappe.session && frappe.session.user && frappe.session.user !== 'Guest') {{
				var userEmail = frappe.session.user;
				var firstName = '{first_name}';
				
				console.log('[GLP1 Intake] Attempting to populate fields for user:', userEmail);
				console.log('[GLP1 Intake] First name to populate:', firstName);
				
				// Populate email field
				var emailField = $('[data-fieldname="email"] input[type="text"], [data-fieldname="email"] input[type="email"], [data-fieldname="email"] .control-value');
				console.log('[GLP1 Intake] Email field selector found', emailField.length, 'elements');
				
				if (emailField.length) {{
					var currentEmail = emailField.val() || emailField.text() || '';
					console.log('[GLP1 Intake] Current email value:', currentEmail);
					
					if (!currentEmail || currentEmail.trim() === '') {{
						if (emailField.is('input')) {{
							emailField.val(userEmail);
							emailField.trigger('change');
							emailField.trigger('input');
							console.log('[GLP1 Intake] ✓ Email field populated (direct input):', userEmail);
						}} else {{
							var actualInput = emailField.closest('.frappe-control').find('input[type="text"], input[type="email"]');
							console.log('[GLP1 Intake] Found nested input for email:', actualInput.length);
							if (actualInput.length) {{
								actualInput.val(userEmail);
								actualInput.trigger('change');
								actualInput.trigger('input');
								console.log('[GLP1 Intake] ✓ Email field populated (nested input):', userEmail);
							}} else {{
								console.log('[GLP1 Intake] ✗ Could not find email input field');
							}}
						}}
					}} else {{
						console.log('[GLP1 Intake] Email field already has value:', currentEmail);
					}}
				}} else {{
					console.log('[GLP1 Intake] ✗ Email field not found in DOM');
					// Try alternative selectors
					var altEmailField = $('input[data-fieldname="email"], input[name="email"]');
					console.log('[GLP1 Intake] Alternative email field selector found', altEmailField.length, 'elements');
				}}
				
				// Populate first_name field
				var firstNameField = $('[data-fieldname="first_name"] input[type="text"], [data-fieldname="first_name"] .control-value');
				console.log('[GLP1 Intake] First name field selector found', firstNameField.length, 'elements');
				
				if (firstNameField.length) {{
					var currentFirstName = firstNameField.val() || firstNameField.text() || '';
					console.log('[GLP1 Intake] Current first name value:', currentFirstName);
					
					if (!currentFirstName || currentFirstName.trim() === '') {{
						if (firstNameField.is('input')) {{
							firstNameField.val(firstName);
							firstNameField.trigger('change');
							firstNameField.trigger('input');
							console.log('[GLP1 Intake] ✓ First name field populated (direct input):', firstName);
						}} else {{
							var actualInput = firstNameField.closest('.frappe-control').find('input[type="text"]');
							console.log('[GLP1 Intake] Found nested input for first name:', actualInput.length);
							if (actualInput.length) {{
								actualInput.val(firstName);
								actualInput.trigger('change');
								actualInput.trigger('input');
								console.log('[GLP1 Intake] ✓ First name field populated (nested input):', firstName);
							}} else {{
								console.log('[GLP1 Intake] ✗ Could not find first name input field');
							}}
						}}
					}} else {{
						console.log('[GLP1 Intake] First name field already has value:', currentFirstName);
					}}
				}} else {{
					console.log('[GLP1 Intake] ✗ First name field not found in DOM');
					// Try alternative selectors
					var altFirstNameField = $('input[data-fieldname="first_name"], input[name="first_name"]');
					console.log('[GLP1 Intake] Alternative first name field selector found', altFirstNameField.length, 'elements');
				}}
			}} else {{
				console.log('[GLP1 Intake] ✗ User not logged in or is Guest');
			}}
		}}
		
		// Try immediately and also after form loads
		console.log('[GLP1 Intake] Scheduling populateFields() calls');
		setTimeout(function() {{ console.log('[GLP1 Intake] Attempt 1 (500ms)'); populateFields(); }}, 500);
		setTimeout(function() {{ console.log('[GLP1 Intake] Attempt 2 (1500ms)'); populateFields(); }}, 1500);
		setTimeout(function() {{ console.log('[GLP1 Intake] Attempt 3 (3000ms)'); populateFields(); }}, 3000);
		
		// Also try when form is ready
		$(document).on('form-ready', function() {{
			console.log('[GLP1 Intake] Form ready event fired');
			populateFields();
		}});
		
		// Try when web form is initialized
		if (typeof frappe.web_form !== 'undefined') {{
			frappe.web_form.on('form-ready', function() {{
				console.log('[GLP1 Intake] Web form ready event fired');
				populateFields();
			}});
		}}
	}});
	</script>
	"""
	
	# Add script to context (will be loaded automatically for standard web forms)
	if not hasattr(context, 'script'):
		context.script = ""
	context.script += populate_script

