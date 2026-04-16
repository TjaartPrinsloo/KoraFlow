"""
KoraFlow Core Hooks
Frappe hooks for branding and module management.
"""

from frappe import _


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

# DocType Class
# from koraflow_core.koraflow_core.doctype.koraflow_module.koraflow_module import KoraFlowModule

# Document Events
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
scheduler_events = {
# 	"all": [
# 		"koraflow_core.koraflow_core.tasks.all"
# 	],
# 	"daily": [
# 		"koraflow_core.koraflow_core.tasks.daily"
# 	],
	"hourly": [
		"koraflow_core.koraflow_core.utils.xero_connector.sync_xero_payments"
	],
# 	"weekly": [
# 		"koraflow_core.koraflow_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"koraflow_core.koraflow_core.tasks.monthly"
# 	]
}

# Testing
# before_tests = "koraflow_core.koraflow_core.install.before_tests"

# After Install
after_install = "koraflow_core.koraflow_core.install.after_install"

# Permission Query Conditions
permission_query_conditions = {
	"Patient Referral": "koraflow_core.koraflow_core.utils.permissions.get_patient_referral_permission_query_conditions",
	"Referral Message": "koraflow_core.koraflow_core.utils.permissions.get_referral_message_permission_query_conditions",
	"Commission Record": "koraflow_core.koraflow_core.utils.permissions.get_commission_record_permission_query_conditions"
}

# Has Permission Checks
has_permission = {
	"Patient Referral": "koraflow_core.koraflow_core.utils.permissions.has_patient_referral_permission",
	"Referral Message": "koraflow_core.koraflow_core.utils.permissions.has_referral_message_permission",
	"Commission Record": "koraflow_core.koraflow_core.utils.permissions.has_commission_record_permission"
}

# Document Events
doc_events = {

	"Patient": {
		"on_update": "koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.sync_patient_name_to_referrals"
	},
	"Delivery Note": {
		"on_submit": "koraflow_core.koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
	},
    "Quotation": {
        "on_submit": "koraflow_core.koraflow_core.utils.xero_connector.sync_quotation"
    },
	"Sales Invoice": {
		"on_submit": [
			"koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.koraflow_core.utils.xero_connector.sync_invoice"
		],
		"on_update_after_submit": [
			"koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.koraflow_core.hooks.commission_hooks.on_invoice_paid"
		],
		"on_update": "koraflow_core.koraflow_core.hooks.commission_hooks.on_invoice_paid"
	}
}

# Overriding Methods
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "koraflow_core.koraflow_core.event.get_events"
# }

# Website Route Overrides - Redirect Sales Agent routes to dashboard
website_route_rules = [
	{"from_route": "/app/sales-agent-dashboard", "to_route": "/app/sales-agent-dash"},
	{"from_route": "/app/build", "to_route": "/app/sales-agent-dash"},
	{"from_route": "/app/home", "to_route": "/app/sales-agent-dash"},
	{"from_route": "/app/user-profile", "to_route": "/app/sales-agent-dash"}
]

# Override workspace sidebar to restrict Sales Agents
override_whitelisted_methods = {
	"frappe.desk.desktop.get_workspace_sidebar_items": "koraflow_core.koraflow_core.utils.workspace_filter.get_workspace_sidebar_items",
	"frappe.website.router.resolve_route": "koraflow_core.koraflow_core.utils.router.resolve_sales_agent_route"
}

# Login hooks
on_login = "koraflow_core.koraflow_core.utils.auth.on_login"
on_session_creation = "koraflow_core.koraflow_core.utils.auth.on_session_creation"
get_website_user_home_page = "koraflow_core.koraflow_core.utils.auth.get_website_user_home_page"

# Before request hook - redirect Sales Agents from /app/build to dashboard
before_request = [
	"koraflow_core.koraflow_core.utils.auth.redirect_sales_agents"
]

# User hooks


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
			"fieldname": "custom_encounter_not_approved",
			"label": "Encounter Not Approved",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "referred_by_sales_agent",
			"hidden": 1
		},
		{
			"fieldname": "custom_rejection_reason_display",
			"label": "Rejection Reason",
			"fieldtype": "Small Text",
			"insert_after": "custom_encounter_not_approved",
			"hidden": 1,
			"read_only": 1
		},
		{
			"fieldname": "custom_rejected_encounter",
			"label": "Rejected Encounter",
			"fieldtype": "Link",
			"options": "Patient Encounter",
			"insert_after": "custom_rejection_reason_display",
			"hidden": 1,
			"read_only": 1
		}
	],
	"Patient Encounter": [
		{
			"fieldname": "custom_encounter_status",
			"label": "Encounter Status",
			"fieldtype": "Select",
			"options": "\nNot Approved",
			"insert_after": "encounter_date",
			"read_only": 1,
			"in_list_view": 0
		},
		{
			"fieldname": "custom_rejection_reason",
			"label": "Rejection Reason",
			"fieldtype": "Small Text",
			"insert_after": "custom_encounter_status",
			"read_only": 1,
			"hidden": 0
		},
		{
			"fieldname": "custom_rejected_by",
			"label": "Rejected By",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "custom_rejection_reason",
			"read_only": 1,
			"hidden": 0
		},
		{
			"fieldname": "custom_rejected_on",
			"label": "Rejected On",
			"fieldtype": "Datetime",
			"insert_after": "custom_rejected_by",
			"read_only": 1,
			"hidden": 0
		}
	]
}
