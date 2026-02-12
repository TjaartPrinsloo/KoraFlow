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
	"/assets/koraflow_core/js/courier_guy_patient.js"
]
app_include_css = [
	"/assets/koraflow_core/css/koraflow_core.css",
	"/assets/koraflow_core/css/sales_agent_dashboard.css"
]

# Scheduled Tasks
scheduler_events = {
	"hourly": [
		"koraflow_core.utils.xero_connector.sync_xero_payments"
	],
}

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
		"on_submit": [
			"koraflow_core.hooks.automation.on_invoice_submit",
			"koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.utils.xero_connector.sync_invoice"
		],
		"on_update_after_submit": [
			"koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.hooks.commission_hooks.on_invoice_paid"
		],
		"on_update": "koraflow_core.hooks.commission_hooks.on_invoice_paid",
		"on_cancel": "koraflow_core.hooks.commission_hooks.cancel_commission_on_invoice_cancel",
		"validate": "koraflow_core.custom_doctype.stock_entry_healthcare.validate_prescription_enforcement"
	},
	"Patient": {
		"on_update": "koraflow_core.doctype.patient_referral.patient_referral.sync_patient_name_to_referrals"
	},
	"Delivery Note": {
		"on_submit": "koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
	},
    "Quotation": {
        "on_submit": "koraflow_core.utils.xero_connector.sync_quotation",
		"on_update_after_submit": [
			"koraflow_core.hooks.healthcare_dispensing_hooks.handle_quotation_acceptance",
			"koraflow_core.hooks.automation.on_quotation_update"
		]
    },
	# GLP-1 Dispensing Workflow  
	"GLP-1 Intake Submission": {
		"on_submit": "koraflow_core.workflows.glp1_dispensing_workflow.handle_intake_submission"
	},
	"GLP-1 Intake Review": {
		"on_update": "koraflow_core.workflows.glp1_dispensing_workflow.handle_nurse_review_approval"
	},
	"GLP-1 Patient Prescription": {
		"on_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_prescription_approval",
		"on_update": "koraflow_core.hooks.automation.on_prescription_status_change",
		"validate": "koraflow_core.hooks.automation.validate_prescription"
	},
	"Stock Entry": {
		"validate": [
			"koraflow_core.custom_doctype.stock_entry_healthcare.validate_stock_entry_healthcare",
			"koraflow_core.hooks.automation.validate_dispense_entry"
		],
		"on_submit": [
			"koraflow_core.hooks.healthcare_dispensing_hooks.handle_pharmacist_approval",
			"koraflow_core.hooks.automation.on_stock_entry_submit"
		]
	},
	"GLP-1 Dispense Confirmation": {
		"on_submit": "koraflow_core.hooks.healthcare_dispensing_hooks.handle_pharmacist_approval"
	},
	# Prescription enforcement on sales documents
	"Sales Order": {
		"validate": "koraflow_core.custom_doctype.stock_entry_healthcare.validate_prescription_enforcement"
	},
	# Prescription generation on encounter submit
	"Patient Encounter": {
		"on_submit": "koraflow_core.hooks.prescription_hooks.handle_encounter_submit"
	},
	# Shipment tracking
	"GLP-1 Shipment": {
		"on_update": "koraflow_core.hooks.automation.on_shipment_update"
	}
}

# Website Route Overrides
website_route_rules = [
	{"from_route": "/app/sales-agent-dashboard", "to_route": "/app/sales-agent-dash"},
	{"from_route": "patient_dashboard", "to_route": "dashboard"},
	{"from_route": "sales_agent_dashboard", "to_route": "sales_agent_dashboard"},
	{"from_route": "app/build", "to_route": "sales_agent_dashboard"},
	{"from_route": "app/home", "to_route": "sales_agent_dashboard"},
	{"from_route": "app/user-profile", "to_route": "sales_agent_dashboard"},
	# Sales Agent Portal routes - map hyphenated URLs to underscore paths
	{"from_route": "/sales-agent-portal", "to_route": "sales_agent_portal"},
	{"from_route": "/sales-agent-portal/banking", "to_route": "sales_agent_portal/banking"},
	{"from_route": "/sales-agent-portal/withdrawal", "to_route": "sales_agent_portal/withdrawal"},
]

# Override workspace sidebar to restrict Sales Agents
override_whitelisted_methods = {
	"frappe.desk.desktop.get_workspace_sidebar_items": "koraflow_core.utils.workspace_filter.get_workspace_sidebar_items",
	"frappe.website.router.resolve_route": "koraflow_core.utils.router.resolve_sales_agent_route",
	"frappe.apps.get_apps": "koraflow_core.api.apps.get_apps"
}

# Login hooks
on_login = "koraflow_core.utils.auth.on_login"

# Session creation hook - runs AFTER set_user_info, so home_page override sticks
on_session_creation = "koraflow_core.utils.auth.on_session_creation"

# Website user home page hook - determines home page for Website Users (Patients)
get_website_user_home_page = "koraflow_core.utils.auth.get_website_user_home_page"

# Before request hook - redirect Sales Agents from /app routes to dashboard
before_request_methods = [
	"koraflow_core.utils.auth.redirect_sales_agents"
]

# Override default signup
after_migrate = [
	"koraflow_core.doctype.user.user_override.override_sign_up",
	"koraflow_core.utils.app_path_fix.fix_app_path"
]

def before_request():
	"""Apply fixes that need to be applied on every request"""
	from koraflow_core.utils.app_path_fix import fix_app_path
	fix_app_path()
	
	import frappe
	# Clear hooks cache intermittently if needed, but not every request for performance
	# frappe.cache.delete_value("app_hooks")
	
	# Execute other before_request methods
	for method in before_request_methods:
		frappe.get_attr(method)()
	
	# Ensure signup override is applied (in case it was reset)
	try:
		from koraflow_core.doctype.user.user_override import override_sign_up
		override_sign_up()
	except:
		pass

before_request = before_request

# Custom Fields
custom_fields = {
	"Patient": [
		{
			"fieldname": "referred_by_sales_agent",
			"label": "Referred By Sales Agent",
			"fieldtype": "Link",
			"options": "Sales Agent",
			"insert_after": "customer"
		},
		{
			"fieldname": "custom_referrer_name",
			"label": "Referrer Name",
			"fieldtype": "Data",
			"insert_after": "referred_by_sales_agent"
		},
		{
			"fieldname": "custom_address_line1",
			"label": "Address Line 1",
			"fieldtype": "Data",
			"insert_after": "custom_referrer_name"
		},
		{
			"fieldname": "custom_address_line2",
			"label": "Address Line 2",
			"fieldtype": "Data",
			"insert_after": "custom_address_line1"
		},
		{
			"fieldname": "custom_city",
			"label": "City",
			"fieldtype": "Data",
			"insert_after": "custom_address_line2"
		},
		{
			"fieldname": "custom_state",
			"label": "State/Province",
			"fieldtype": "Data",
			"insert_after": "custom_city"
		},
		{
			"fieldname": "custom_pincode",
			"label": "Postal Code",
			"fieldtype": "Data",
			"insert_after": "custom_state"
		},
		{
			"fieldname": "custom_country",
			"label": "Country",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "custom_pincode"
		},
		{
			"fieldname": "custom_height_cm",
			"label": "Height (cm)",
			"fieldtype": "Float",
			"insert_after": "dob"
		},
		{
			"fieldname": "custom_target_weight",
			"label": "Target Weight",
			"fieldtype": "Float",
			"insert_after": "custom_height_cm"
		},
		{
			"fieldname": "custom_height_unit",
			"label": "Height Unit",
			"fieldtype": "Select",
			"options": "\nFeet/Inches\nCentimeters",
			"insert_after": "custom_target_weight"
		},
		{
			"fieldname": "custom_weight_unit",
			"label": "Weight Unit",
			"fieldtype": "Select",
			"options": "\nPounds\nKilograms",
			"insert_after": "custom_height_unit"
		},
		{
			"fieldname": "custom_bmi",
			"label": "BMI",
			"fieldtype": "Float",
			"insert_after": "custom_weight_unit"
		}
	]
}
