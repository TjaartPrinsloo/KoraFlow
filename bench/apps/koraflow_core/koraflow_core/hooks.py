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
app_include_js = "/assets/koraflow_core/js/koraflow_core.js"
app_include_css = "/assets/koraflow_core/css/koraflow_core.css"

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
# scheduler_events = {
# 	"all": [
# 		"koraflow_core.koraflow_core.tasks.all"
# 	],
# 	"daily": [
# 		"koraflow_core.koraflow_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"koraflow_core.koraflow_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"koraflow_core.koraflow_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"koraflow_core.koraflow_core.tasks.monthly"
# 	]
# }

# Testing
# before_tests = "koraflow_core.koraflow_core.install.before_tests"

# Overriding Methods
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "koraflow_core.koraflow_core.event.get_events"
# }

