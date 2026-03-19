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

# ======================================================
# BRANDING: Override the default Frappe logo with S2W
# Frappe's get_app_logo() picks the LAST entry in hooks,
# so this custom app's value overrides frappe/hooks.py
# ======================================================
app_logo_url = "/assets/koraflow_core/images/s2w_logo.png"

# Include JS, CSS files in bundle
app_include_js = [
	"/assets/koraflow_core/js/koraflow_core.js?v=20260318j",
	"/assets/koraflow_core/js/sales_agent_dashboard.js",
	"/assets/koraflow_core/js/courier_guy_delivery_note.js",
	"/assets/koraflow_core/js/courier_guy_patient.js",
	"/assets/koraflow_core/js/courier_guy_dashboard.js?v=20260316a"
]
app_include_css = [
	"/assets/koraflow_core/css/koraflow_core.css",
	"/assets/koraflow_core/css/sales_agent_dashboard.css",
	"/assets/koraflow_core/css/courier_guy_dashboard.css?v=20260316a"
]

# Scheduled Tasks
scheduler_events = {
	"hourly": [
		"koraflow_core.utils.xero_connector.sync_xero_payments",
		"koraflow_core.utils.xero_connector.sync_xero_quotes"
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
	"GLP-1 Pharmacy Dispense Task": "koraflow_core.utils.glp1_permissions.get_glp1_dispense_task_permission_query_conditions",
	# Nurse Role Permissions
	"Patient Appointment": "koraflow_core.permissions.get_nurse_appointment_conditions",
	"Patient": "koraflow_core.permissions.get_nurse_patient_conditions",
	"Issue": "koraflow_core.permissions.get_nurse_issue_conditions"
}

# Has Permission Checks
has_permission = {
	"Patient Referral": "koraflow_core.utils.permissions.has_patient_referral_permission",
	"Referral Message": "koraflow_core.utils.permissions.has_referral_message_permission",
	"Commission Record": "koraflow_core.utils.permissions.has_commission_record_permission",
	# GLP-1 Permissions
	"GLP-1 Patient Prescription": "koraflow_core.utils.glp1_permissions.has_glp1_prescription_permission",
	"GLP-1 Pharmacy Dispense Task": "koraflow_core.utils.glp1_permissions.has_glp1_dispense_task_permission",
	# Nurse Role Permissions
	"Patient": "koraflow_core.permissions.patient_has_permission",
	"Issue": "koraflow_core.permissions.issue_has_permission"
}

# Document Events
doc_events = {
	"Sales Invoice": {
		"validate": "koraflow_core.hooks.commission_hooks.populate_sales_partner",
		"on_submit": [
			"koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.koraflow_core.doctype.commission_record.commission_record.create_commission_from_invoice",
			"koraflow_core.hooks.automation.on_invoice_submit",
			"koraflow_core.utils.xero_connector.sync_invoice"
		],
		"on_cancel": [
			"koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.update_referral_on_invoice_paid",
			"koraflow_core.koraflow_core.doctype.commission_record.commission_record.cancel_commission_from_invoice"
		]
	},
	"Patient": {
		"on_update": [
			"koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.sync_patient_name_to_referrals",
			"koraflow_core.hooks.patient_hooks.sync_address_and_contact"
		]
	},
	"Delivery Note": {
		"on_submit": "koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
	},
	"Payment Entry": {
		"on_submit": [
			"koraflow_core.hooks.commission_hooks.on_payment_entry_submit",
			"koraflow_core.hooks.fulfilment_hooks.on_payment_received"
		]
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
		"on_submit": "koraflow_core.hooks.prescription_hooks.handle_encounter_submit",
		"before_submit": "koraflow_core.permissions.block_nurse_submit",
		"on_update": "koraflow_core.notifications.notify_doctor_of_draft"
	},
	# Shipment tracking
	"GLP-1 Shipment": {
		"on_update": "koraflow_core.hooks.automation.on_shipment_update"
	},
	"Customer": {
		"after_insert": "koraflow_core.utils.xero_connector.sync_customer_to_xero"
	},
	"User": {
		"after_insert": "koraflow_core.permissions.after_insert_user"
	},
	"Workspace": {
		"onload": "koraflow_core.utils.workspace_filter.filter_healthcare_workspace"
	}

}

# Custom Scripts for DocTypes
doctype_js = {
    "Patient": "public/js/patient.js",
    "Patient Appointment": "public/js/nurse_appointment.js",
    "Patient Encounter": "public/js/nurse_encounter.js",
    "Customer": "public/js/xero_customer.js",
    "User": "public/js/user.js",
    "GLP-1 Intake Submission": "koraflow_core/doctype/glp1_intake_submission/glp1_intake_submission.js",
    "GLP-1 Intake Review": "koraflow_core/doctype/glp_1_intake_review/glp_1_intake_review.js",
    "Sales Invoice": "public/js/sales_invoice.js"
}

# Custom Dashboards
override_doctype_dashboards = {
    "Patient": "koraflow_core.overrides.patient_dashboard.get_data"
}

# Website Route Overrides
website_route_rules = [
	{"from_route": "/app/sales-agent-dashboard", "to_route": "/app/sales-agent-dash"},
	{"from_route": "/patient_dashboard", "to_route": "dashboard"},
	{"from_route": "/sales_agent_dashboard", "to_route": "sales_agent_dashboard"},
	{"from_route": "/app/build", "to_route": "sales_agent_dashboard"},
	{"from_route": "/app/home", "to_route": "sales_agent_dashboard"},
	{"from_route": "/app/user-profile", "to_route": "sales_agent_dashboard"},
	# Sales Agent Portal routes - map hyphenated URLs to underscore paths
	{"from_route": "/sales-agent-portal", "to_route": "sales_agent_portal"},
	{"from_route": "/sales-agent-portal/banking", "to_route": "sales_agent_portal/banking"},
	{"from_route": "/sales-agent-portal/withdrawal", "to_route": "sales_agent_portal/withdrawal"},
	{"from_route": "/glp1_intake_wizard", "to_route": "intake"},
	{"from_route": "/glp1-intake-wizard", "to_route": "intake"},
	{"from_route": "/glp1-intake", "to_route": "intake"},
]

# Override workspace sidebar to restrict Sales Agents
override_whitelisted_methods = {
	"frappe.desk.desktop.get_workspace_sidebar_items": "koraflow_core.utils.workspace_filter.get_workspace_sidebar_items",
	"frappe.desk.desktop.get_desktop_page": "koraflow_core.utils.workspace_filter.get_desktop_page",
	"frappe.website.router.resolve_route": "koraflow_core.utils.router.resolve_sales_agent_route",
	"frappe.apps.get_apps": "koraflow_core.api.apps.get_apps"
}

# Login hooks
on_login = "koraflow_core.utils.auth.on_login"
on_logout = "koraflow_core.utils.auth.on_logout"

# Session creation hook - runs AFTER set_user_info, so home_page override sticks
on_session_creation = "koraflow_core.utils.auth.on_session_creation"

# Website user home page hook - determines home page for Website Users (Patients)
get_website_user_home_page = "koraflow_core.utils.auth.get_website_user_home_page"

# Before request hook - redirect Sales Agents and Patients from /app routes
before_request = [
	"koraflow_core.utils.auth.redirect_sales_agents",
	"koraflow_core.utils.auth.redirect_patients"
]

# Override default signup
after_migrate = [
	"koraflow_core.utils.user_override.override_sign_up",
	"koraflow_core.utils.app_path_fix.fix_app_path",
	"koraflow_core.install.apply_property_setters",
	"koraflow_core.install.setup_commission_report_shortcuts"
]

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
			"fieldname": "custom_is_existing_patient",
			"label": "Existing Patient (Returning)",
			"fieldtype": "Check",
			"insert_after": "custom_referrer_name",
			"default": 0,
			"in_list_view": 1,
			"in_standard_filter": 1,
			"description": "Patient self-identified as a returning Slim2Well patient during intake"
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
		},
		{
			"fieldname": "custom_assigned_nurse",
			"label": "Assigned Nurse",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "custom_bmi",
			"description": "Clinical nurse assigned to this patient for portal support."
		}
	],
	"Quotation": [
		{
			"fieldname": "custom_courier_rate",
			"label": "Courier Rate",
			"fieldtype": "Currency",
			"insert_after": "custom_prescription",
			"read_only": 1,
			"description": "Actual TCG shipping rate used"
		},
		{
			"fieldname": "custom_courier_service_level",
			"label": "Courier Service Level",
			"fieldtype": "Data",
			"insert_after": "custom_courier_rate",
			"read_only": 1,
			"description": "TCG service level code (e.g. ECO)"
		},
		{
			"fieldname": "custom_xero_quote_id",
			"label": "Xero Quote ID",
			"fieldtype": "Data",
			"insert_after": "custom_courier_service_level",
			"read_only": 1,
			"hidden": 1,
			"description": "Xero Quote ID for bi-directional sync"
		}
	],
	"Sales Invoice": [
		{
			"fieldname": "custom_xero_invoice_id",
			"label": "Xero Invoice ID",
			"fieldtype": "Data",
			"insert_after": "remarks",
			"read_only": 1,
			"hidden": 1,
			"description": "Xero Invoice ID for bi-directional sync"
		},
		{
			"fieldname": "custom_xero_invoice_number",
			"label": "Xero Invoice Number",
			"fieldtype": "Data",
			"insert_after": "custom_xero_invoice_id",
			"read_only": 1,
			"hidden": 1,
			"description": "Xero Invoice Number"
		},
		{
			"fieldname": "custom_xero_status",
			"label": "Xero Status",
			"fieldtype": "Data",
			"insert_after": "custom_xero_invoice_number",
			"read_only": 1,
			"description": "Current status in Xero (AUTHORISED, PAID, VOIDED)"
		},
		{
			"fieldname": "custom_xero_voided",
			"label": "Voided in Xero",
			"fieldtype": "Check",
			"insert_after": "custom_xero_status",
			"read_only": 1,
			"default": 0
		}
	],
	"Customer": [
		{
			"fieldname": "custom_xero_section",
			"label": "Xero Integration",
			"fieldtype": "Section Break",
			"insert_after": "default_currency",
			"collapsible": 1
		},
		{
			"fieldname": "custom_xero_contact_id",
			"label": "Xero Contact ID",
			"fieldtype": "Data",
			"insert_after": "custom_xero_section",
			"read_only": 1,
			"description": "Xero Contact ID for bi-directional sync"
		},
		{
			"fieldname": "custom_is_xero_customer",
			"label": "Imported from Xero",
			"fieldtype": "Check",
			"insert_after": "custom_xero_contact_id",
			"read_only": 1,
			"default": 0,
			"description": "Customer was imported from Xero (no portal account or intake form initially)"
		},
		{
			"fieldname": "custom_xero_sync_date",
			"label": "Last Xero Sync",
			"fieldtype": "Datetime",
			"insert_after": "custom_is_xero_customer",
			"read_only": 1
		},
		{
			"fieldname": "custom_xero_col",
			"fieldtype": "Column Break",
			"insert_after": "custom_xero_sync_date"
		},
		{
			"fieldname": "custom_intake_required",
			"label": "Intake Form Required",
			"fieldtype": "Check",
			"insert_after": "custom_xero_col",
			"default": 0,
			"description": "When checked, intake form must be completed before treatment"
		},
		{
			"fieldname": "custom_intake_completed",
			"label": "Intake Form Completed",
			"fieldtype": "Check",
			"insert_after": "custom_intake_required",
			"read_only": 1,
			"default": 0
		}
	],
	"Issue": [
		{
			"fieldname": "custom_patient",
			"label": "Patient",
			"fieldtype": "Link",
			"options": "Patient",
			"insert_after": "customer",
			"in_list_view": 1
		},
		{
			"fieldname": "custom_is_portal_ticket",
			"label": "Is Portal Ticket",
			"fieldtype": "Check",
			"insert_after": "custom_patient",
			"default": 0
		}
	],
	"Healthcare Practitioner": [
		{
			"fieldname": "custom_signature_image",
			"label": "Digital Signature",
			"fieldtype": "Attach Image",
			"insert_after": "prescription_print_format",
			"description": "Upload a scanned or digital signature for prescriptions (SAHPRA compliance)"
		}
	]
}
