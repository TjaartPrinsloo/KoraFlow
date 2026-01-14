"""
Add GLP-1 Intake Form child table field to Patient DocType
"""
import frappe


def execute():
	"""Add custom field to Patient DocType"""
	# Check if custom field already exists
	if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}):
		return
	
	# Create custom field
	custom_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Patient",
		"fieldname": "glp1_intake_forms",
		"fieldtype": "Table",
		"options": "GLP-1 Intake Submission",
		"label": "GLP-1 Intake Forms",
		"insert_after": "medical_history_tab",
		"allow_in_quick_entry": 0,
		"in_list_view": 0,
		"in_standard_filter": 0,
		"in_global_search": 0,
		"read_only": 0,
		"reqd": 0,
		"translatable": 0
	})
	
	custom_field.insert(ignore_permissions=True)
	frappe.db.commit()
	
	frappe.msgprint("Added GLP-1 Intake Forms field to Patient DocType")

