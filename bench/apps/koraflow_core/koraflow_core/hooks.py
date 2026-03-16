app_name = "koraflow_core"
app_title = "KoraFlow Core"
app_publisher = "KoraFlow Team"
app_description = "KoraFlow Core - White-label modular enterprise platform"
app_email = "team@koraflow.io"
app_license = "MIT"
app_logo_url = "/assets/koraflow_core/images/s2w_logo.png"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "koraflow_core",
# 		"logo": "/assets/koraflow_core/logo.png",
# 		"title": "KoraFlow Core",
# 		"route": "/koraflow_core",
# 		"has_permission": "koraflow_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/koraflow_core/css/koraflow_core.css"
# app_include_js = "/assets/koraflow_core/js/koraflow_core.js"

# include js, css files in header of web template
# web_include_css = "/assets/koraflow_core/css/koraflow_core.css"
# web_include_js = "/assets/koraflow_core/js/koraflow_core.js"

# Custom Scripts for Patient DocType
doctype_js = {
    "Patient": "public/js/patient.js",
    "GLP-1 Intake Submission": "koraflow_core/doctype/glp1_intake_submission/glp1_intake_submission.js",
    "GLP-1 Intake Review": "koraflow_core/doctype/glp_1_intake_review/glp_1_intake_review.js"
}

# Document Events
doc_events = {
	"Sales Invoice": {
		"on_update": "koraflow_core.hooks.commission_hooks.on_invoice_paid",
		"on_submit": "koraflow_core.hooks.commission_hooks.on_invoice_paid"
	}
}

override_doctype_dashboards = {
    "Patient": "koraflow_core.overrides.patient_dashboard.get_data"
}


override_whitelisted_methods = {
    "frappe.apps.get_apps": "koraflow_core.overrides.apps.get_apps"
}
