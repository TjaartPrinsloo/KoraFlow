"""
Add AI-Generated Medical Summary field to Patient DocType
"""
import frappe


def execute():
	"""Add custom field to Patient DocType for storing AI-generated medical summary"""
	# Check if custom field already exists
	if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}):
		return
	
	# Create custom field
	custom_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Patient",
		"fieldname": "ai_medical_summary",
		"fieldtype": "Text Editor",
		"label": "AI Medical Summary",
		"description": "AI-generated medical summary from patient intake form review. This summary includes patient overview, medical history, contraindications, and recommendations for medical staff review.",
		"insert_after": "glp1_intake_forms",
		"allow_in_quick_entry": 0,
		"in_list_view": 0,
		"in_standard_filter": 0,
		"in_global_search": 0,
		"read_only": 1,  # Read-only as it's AI-generated
		"reqd": 0,
		"translatable": 0,
		"depends_on": "eval:doc.glp1_intake_forms && doc.glp1_intake_forms.length > 0"
	})
	
	custom_field.insert(ignore_permissions=True)
	frappe.db.commit()
	
	frappe.msgprint("Added AI Medical Summary field to Patient DocType")

