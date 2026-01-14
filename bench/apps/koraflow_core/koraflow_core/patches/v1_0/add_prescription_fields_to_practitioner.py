"""
Add Prescription Template and Practice Details fields to Healthcare Practitioner
"""
import frappe


def execute():
	"""Add custom fields to Healthcare Practitioner for prescription generation"""
	
	custom_fields = [
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "prescription_section",
			"fieldtype": "Section Break",
			"label": "Prescription Settings",
			"insert_after": "primary_address",
			"collapsible": 1
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "practice_number",
			"fieldtype": "Data",
			"label": "Practice Number",
			"description": "Practice registration number for SAHPRA compliance",
			"insert_after": "prescription_section",
			"reqd": 0
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "hpcsa_registration_number",
			"fieldtype": "Data",
			"label": "HPCSA Registration Number",
			"description": "Health Professions Council of South Africa registration number",
			"insert_after": "practice_number",
			"reqd": 0
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "practice_address",
			"fieldtype": "Small Text",
			"label": "Practice Physical Address",
			"description": "Physical address of the practice for prescription requirements",
			"insert_after": "hpcsa_registration_number",
			"reqd": 0
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "column_break_prescription",
			"fieldtype": "Column Break",
			"insert_after": "practice_address"
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "prescription_template",
			"fieldtype": "Attach",
			"label": "Blank Prescription Template",
			"description": "Upload blank prescription template PDF (for reference/layout)",
			"insert_after": "column_break_prescription",
			"reqd": 0
		},
		{
			"dt": "Healthcare Practitioner",
			"fieldname": "prescription_print_format",
			"fieldtype": "Link",
			"label": "Prescription Print Format",
			"description": "Print Format to use for generating prescriptions (defaults to SAHPRA Prescription if not set)",
			"options": "Print Format",
			"insert_after": "prescription_template",
			"reqd": 0
		}
	]
	
	for field_data in custom_fields:
		fieldname = field_data["fieldname"]
		doctype = field_data["dt"]
		
		# Check if custom field already exists
		if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
			frappe.logger().info(f"Custom field {fieldname} already exists for {doctype}")
			continue
		
		# Create custom field
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"owner": "Administrator",
			**field_data
		})
		
		custom_field.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"Created custom field: {fieldname} for {doctype}")
	
	frappe.msgprint("Added prescription fields to Healthcare Practitioner DocType")
