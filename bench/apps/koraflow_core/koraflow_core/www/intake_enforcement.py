"""
Intake enforcement middleware for portal pages
Blocks portal access until intake form is completed
"""
import frappe
from frappe import _

# Apply TemplatePage patch on first request
try:
	from koraflow_core.utils.website_path_resolver import patch_template_page
	patch_template_page()
except Exception:
	# Silently fail if patch can't be applied
	pass



def check_intake_completion():
	"""
	Check if user has completed intake form.
	Redirect to intake form if not completed.
	This is called via website hooks.
	"""
	# Debug logging
	if frappe.session.user == "chris@koraflow.com":
		frappe.log_error(title="Intake Check Start", message=f"User: {frappe.session.user}, Path: {frappe.request.path}")

	# Skip for guest users, system users, and admin pages
	if frappe.session.user == "Guest":
		return
	
	# Skip for system users (they don't need intake)
	if "System User" in frappe.get_roles():
		return
	
	# Skip for Sales Partners (they don't need intake)
	if "Sales Partner Portal" in frappe.get_roles():
		return
	
	# Only enforce for Patient role
	if "Patient" not in frappe.get_roles():
		return
	
	# Skip for admin pages (/app, /desk, etc.)
	if frappe.request.path.startswith("/app") or frappe.request.path.startswith("/desk"):
		return
	
	# Skip for login, signup, password reset, and verification pages
	allowed_paths = [
		"/login",
		"/s2w_login",
		"/signup",
		"/update-password",
		"/verify-email",
		"/glp1-intake",
		"/intake",  # Route alias for glp1-intake
		"/glp1-intake-wizard",
		"/my-referrals",  # Sales Partner portal pages
		"/my-commissions",  # Sales Partner portal pages
		"/api/",
		"/assets/",
		"/files/",
		"/privacy",  # Legal pages
		"/terms",
		"/legal",
		"/sahpra",
		"/cookies",
	]
	
	if any(frappe.request.path.startswith(path) for path in allowed_paths):
		return
	
	# Check intake completion
	user = frappe.get_doc("User", frappe.session.user)
	
	# If email not verified, allow access to verification and password setup only
	if not user.get("email_verified"):
		if frappe.request.path not in ["/verify-email", "/update-password"]:
			# Don't redirect, just allow - they'll be prompted to verify email
			return
	
	# Check intake completion
	intake_completed = user.get("intake_completed", 0)
	
	if not intake_completed:
		# Redirect to intake form
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/intake"
		return

