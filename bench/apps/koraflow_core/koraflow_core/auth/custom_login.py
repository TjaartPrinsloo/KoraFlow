"""
Custom Login Manager to allow temporary login for disabled Patient users
This allows patients to fill intake form even when their account is disabled
"""
import frappe
from frappe import _


def apply_login_override():
	"""Monkey patch LoginManager.authenticate to allow temporary login for disabled Patient users"""
	from frappe.auth import LoginManager
	
	# Store original authenticate method
	original_authenticate = LoginManager.authenticate
	
	def custom_authenticate(self, user: str | None = None, pwd: str | None = None):
		from frappe.core.doctype.user.user import User
		
		if not (user and pwd):
			user, pwd = frappe.form_dict.get("usr"), frappe.form_dict.get("pwd")
		if not (user and pwd):
			self.fail(_("Incomplete login details"), user=user)
		
		from frappe.auth import MAX_PASSWORD_SIZE
		if len(pwd) > MAX_PASSWORD_SIZE:
			self.fail(_("Password size exceeded the maximum allowed size"), user=user)
		
		_raw_user_name = user
		user = User.find_by_credentials(user, pwd)
		
		from frappe.auth import get_login_attempt_tracker
		ip_tracker = get_login_attempt_tracker(frappe.local.request_ip)
		if not user:
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("Invalid login credentials", user=_raw_user_name)
		
		from frappe.auth import should_run_2fa
		ignore_tracker = should_run_2fa(user.name) and ("otp" in frappe.form_dict)
		user_tracker = None if ignore_tracker else get_login_attempt_tracker(user.name)
		
		if not user.is_authenticated:
			user_tracker and user_tracker.add_failure_attempt()
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("Invalid login credentials", user=user.name)
		
		# Allow disabled Patient users if they have a temporary login token
		# This allows them to fill the intake form
		allow_disabled_login = False
		if user.user_type == "Patient" and not user.enabled:
			# Check if this is a temporary login via signup token
			# The token is passed via form_dict or request args
			token = frappe.form_dict.get("signup_token") or (
				frappe.request.args.get("signup_token") if hasattr(frappe, 'request') and frappe.request else None
			)
			if token:
				# Verify token exists in cache
				login_data = frappe.cache.get_value(f"signup_auto_login:{token}")
				if login_data and login_data.get("user") == user.name:
					allow_disabled_login = True
					frappe.logger().info(f"Allowing temporary login for disabled Patient user: {user.name}")
			# Also check if user is currently logged in via temporary session
			# This allows them to continue using the form after initial login
			elif hasattr(frappe.local, 'flags') and frappe.local.flags.get('temporary_patient_login'):
				allow_disabled_login = True
		
		if not (user.name == "Administrator" or user.enabled or allow_disabled_login):
			user_tracker and user_tracker.add_failure_attempt()
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("User disabled or missing", user=user.name)
		else:
			user_tracker and user_tracker.add_success_attempt()
			ip_tracker and ip_tracker.add_success_attempt()
		
		self.user = user.name
		
		# Set flag to indicate this is a temporary login
		if allow_disabled_login:
			frappe.local.flags.temporary_patient_login = True
	
	# Replace the authenticate method
	LoginManager.authenticate = custom_authenticate


# Apply the override when module is imported
try:
	apply_login_override()
except Exception as e:
	frappe.log_error(title="Login Override", message=f"Error applying login override: {e}")
