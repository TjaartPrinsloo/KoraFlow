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
doc_events = {
	"GLP1 Intake Form": {
		"on_update": "koraflow_core.koraflow_core.utils.patient_sync.update_patient_uid",
		"on_submit": "koraflow_core.koraflow_core.utils.patient_sync.update_patient_uid"
	}
}

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
	"Sales Invoice": {
		"on_submit": [
            "koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
            "koraflow_core.koraflow_core.utils.xero_connector.sync_invoice"
        ],
		"on_update_after_submit": "koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid"
	},
	"Patient": {
		"on_update": "koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.sync_patient_name_to_referrals"
	},
	"Delivery Note": {
		"on_submit": "koraflow_core.koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
	},
    "Quotation": {
        "on_submit": "koraflow_core.koraflow_core.utils.xero_connector.sync_quotation"
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

# Before request hook - redirect Sales Agents from /app/build to dashboard
before_request = "koraflow_core.koraflow_core.utils.auth.redirect_sales_agents"

