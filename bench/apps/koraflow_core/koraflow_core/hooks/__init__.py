# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
KoraFlow Core Hooks
Frappe hooks for branding and module management.
"""

from frappe import _

# Override email sending for development (prevents SMTP errors)
# Use string path that Frappe's hook system expects (list format)
override_email_send = ["koraflow_core.utils.email_override.override_email_send"]


def get_branding_map():
    """
    Central branding mapping dictionary.
    Maps original Frappe/ERPNext names to KoraFlow names.
    """
    return {
        # Core Framework
        'Frappe': 'KoraFlow Core',
        'frappe': 'KoraFlow Core',
        
        # Main Products
        'ERPNext': 'KoraFlow ERP',
        'erpnext': 'KoraFlow ERP',
        
        # Modules
        'ERPNext Healthcare': 'KoraFlow Healthcare',
        'healthcare': 'KoraFlow Healthcare',
        'Healthcare': 'KoraFlow Healthcare',
        
        'ERPNext HR': 'KoraFlow Workforce',
        'hr': 'KoraFlow Workforce',
        'HR': 'KoraFlow Workforce',
        
        'ERPNext CRM': 'KoraFlow CRM',
        'crm': 'KoraFlow CRM',
        'CRM': 'KoraFlow CRM',
        
        'ERPNext Helpdesk': 'KoraFlow Support',
        'helpdesk': 'KoraFlow Support',
        'Helpdesk': 'KoraFlow Support',
        
        'ERPNext Insights': 'KoraFlow Insights',
        'insights': 'KoraFlow Insights',
        'Insights': 'KoraFlow Insights',
    }


def get_branded_name(original_name):
    """
    Get branded name for a given original name.
    Returns original name if no mapping exists.
    """
    branding_map = get_branding_map()
    return branding_map.get(original_name, original_name)


# Frappe hooks
app_name = "koraflow_core"
app_title = "KoraFlow Core"
app_publisher = "KoraFlow Team"
app_description = "Core module for KoraFlow platform"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "team@koraflow.io"
app_license = "MIT"

# Include JS, CSS files in bundle
app_include_js = [
	"/assets/koraflow_core/js/koraflow_core.js",
	"/assets/koraflow_core/js/sales_agent_dashboard.js",
	"/assets/koraflow_core/js/courier_guy_delivery_note.js",
	"/assets/koraflow_core/js/courier_guy_patient.js",
	"/assets/koraflow_core/js/courier_guy_workspace_hook.js",
	# Removed: "/assets/koraflow_core/js/courier_guy_dashboard.js" - loaded dynamically by workspace hook
	"/assets/koraflow_core/js/courier_guy_sidebar_logo.js",
	"/assets/koraflow_core/js/patient.js"
]

# Include JS files on website/login pages
web_include_js = [
	"/assets/koraflow_core/js/signup_form.js?v=4"
]
app_include_css = [
	"/assets/koraflow_core/css/koraflow_core.css",
	"/assets/koraflow_core/css/sales_agent_dashboard.css",
	"/assets/koraflow_core/css/courier_guy_dashboard.css"
]

# DocType specific JavaScript
doctype_js = {
	"Patient": "public/js/patient.js"
}

# Page specific JavaScript (for workspaces accessed as pages)
page_js = {
	"Courier Guy": "public/js/courier_guy_workspace_hook.js"
}

# DocType Class
# from koraflow_core.doctype.koraflow_module.koraflow_module import KoraFlowModule

# Document Events
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# scheduler_events = {
# 	"all": [
# 		"koraflow_core.tasks.all"
# 	],
# 	"daily": [
# 		"koraflow_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"koraflow_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"koraflow_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"koraflow_core.tasks.monthly"
# 	]
# }

# Testing
# before_tests = "koraflow_core.install.before_tests"

# After Install
after_install = "koraflow_core.install.after_install"

# Permission Query Conditions
permission_query_conditions = {
	"Patient Referral": "koraflow_core.utils.permissions.get_patient_referral_permission_query_conditions",
	"Referral Message": "koraflow_core.utils.permissions.get_referral_message_permission_query_conditions",
	"Commission Record": "koraflow_core.utils.permissions.get_commission_record_permission_query_conditions",
	# GLP-1 Permissions
	"GLP-1 Patient Prescription": "koraflow_core.utils.glp1_permissions.get_glp1_prescription_permission_query_conditions",
	"GLP-1 Pharmacy Dispense Task": "koraflow_core.utils.glp1_permissions.get_glp1_dispense_task_permission_query_conditions"
}

# Has Permission Checks
has_permission = {
	"Patient Referral": "koraflow_core.utils.permissions.has_patient_referral_permission",
	"Referral Message": "koraflow_core.utils.permissions.has_referral_message_permission",
	"Commission Record": "koraflow_core.utils.permissions.has_commission_record_permission",
	# GLP-1 Permissions
	"GLP-1 Patient Prescription": "koraflow_core.utils.glp1_permissions.has_glp1_prescription_permission",
	"GLP-1 Pharmacy Dispense Task": "koraflow_core.utils.glp1_permissions.has_glp1_dispense_task_permission"
}

# Document Events
doc_events = {
	"Sales Invoice": {
		"on_submit": "koraflow_core.hooks.commission_hooks.calculate_commission_on_invoice",
		"on_update_after_submit": "koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
		"on_cancel": "koraflow_core.hooks.commission_hooks.cancel_commission_on_invoice_cancel"
	},
	"Patient": {
		"on_update": "koraflow_core.doctype.patient_referral.patient_referral.sync_patient_name_to_referrals"
	},
	"Delivery Note": {
		"on_submit": "koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
	},
	# GLP-1 Dispensing Workflow
	"GLP-1 Intake Submission": {
		"on_submit": "koraflow_core.workflows.glp1_dispensing_workflow.handle_intake_submission"
	},
	"GLP-1 Intake Review": {
		"on_update": "koraflow_core.workflows.glp1_dispensing_workflow.handle_nurse_review_approval"
	},
	"GLP-1 Patient Prescription": {
		"on_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_prescription_approval"
	},
	"Quotation": {
		"on_update_after_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_quotation_acceptance"
	},
	"Stock Entry": {
		"validate": "koraflow_core.custom_doctype.stock_entry_healthcare.validate_stock_entry_healthcare",
		"on_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_pharmacist_approval"
	},
	"GLP-1 Dispense Confirmation": {
		"on_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_pharmacist_approval"
	},
	# Prescription enforcement on sales documents
	"Sales Order": {
		"validate": "koraflow_core.custom_doctype.stock_entry_healthcare.validate_prescription_enforcement"
	},
	"Sales Invoice": {
		"validate": "koraflow_core.custom_doctype.stock_entry_healthcare.validate_prescription_enforcement"
	},
	# Prescription generation on encounter submit
	"Patient Encounter": {
		"on_submit": "koraflow_core.hooks.prescription_hooks.generate_prescription_on_encounter_submit"
	}
}

# Overriding Methods
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "koraflow_core.event.get_events"
# }

# Website Route Overrides
website_route_rules = [
	{"from_route": "/app/sales-agent-dashboard", "to_route": "/app/sales-agent-dash"}
]

# Override workspace sidebar to restrict Sales Agents
override_whitelisted_methods = {
	"frappe.desk.desktop.get_workspace_sidebar_items": "koraflow_core.utils.workspace_filter.get_workspace_sidebar_items",
	"frappe.apps.get_apps": "koraflow_core.api.apps.get_apps"
}

# Login hooks
on_login = "koraflow_core.utils.auth.on_login"

# Override default signup
after_migrate = "koraflow_core.doctype.user.user_override.override_sign_up"

# Override email sending for development (prevents SMTP errors)
# Function is loaded via _load_email_override() below

# Fix app path resolution for TemplatePage
# Applied after migrations and on every request (since frappe.init(force=True) resets things)
after_migrate = [
	"koraflow_core.doctype.user.user_override.override_sign_up",
	"koraflow_core.utils.app_path_fix.fix_app_path"
]

# Apply app path fix on every request (frappe.init(force=True) resets the patch)
# Also ensure signup override is applied on every request
def before_request():
	"""Apply fixes that need to be applied on every request"""
	# #region agent log
	import json, os
	log_path = "/Users/tjaartprinsloo/Documents/KoraFlow/.cursor/debug.log"
	try:
		with open(log_path, "a") as f:
			f.write(json.dumps({"id":"log_before_1","timestamp":int(__import__("time").time()*1000),"location":"hooks.py:before_request","message":"before_request called","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
	except: pass
	# #endregion
	
	from koraflow_core.utils.app_path_fix import fix_app_path
	fix_app_path()
	
	# Clear hooks cache and patch email override path
	try:
		import frappe
		if hasattr(frappe, 'cache'):
			frappe.cache.delete_value("app_hooks")
		
		# Patch get_hook_method to handle email override correctly
		# This ensures even if hooks are cached with wrong path, we fix it
		from frappe.utils import get_hook_method as original_get_hook_method
		
		def patched_get_hook_method(hook_name, fallback=None):
			if hook_name == "override_email_send":
				# Always use the correct path for email override
				try:
					from koraflow_core.utils.email_override import override_email_send
					return override_email_send
				except ImportError:
					# Fallback to original if import fails
					pass
			# For other hooks, use original function
			return original_get_hook_method(hook_name, fallback)
		
		# Only patch if not already patched
		if not hasattr(frappe.utils, '_original_get_hook_method'):
			frappe.utils._original_get_hook_method = original_get_hook_method
			frappe.utils.get_hook_method = patched_get_hook_method
		
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_before_cache","timestamp":int(__import__("time").time()*1000),"location":"hooks.py:before_request","message":"Hooks cache cleared and patched","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
	except Exception as e:
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_before_cache_err","timestamp":int(__import__("time").time()*1000),"location":"hooks.py:before_request","message":"Failed to clear cache/patch","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
		pass
	
	# Ensure signup override is applied (in case it was reset)
	try:
		from koraflow_core.doctype.user.user_override import override_sign_up
		result = override_sign_up()
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_before_2","timestamp":int(__import__("time").time()*1000),"location":"hooks.py:before_request","message":"Override applied in before_request","data":{"success":result is not None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
	except Exception as e:
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_before_3","timestamp":int(__import__("time").time()*1000),"location":"hooks.py:before_request","message":"Override failed in before_request","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
		# Silently fail if override can't be applied
		pass

before_request = before_request
