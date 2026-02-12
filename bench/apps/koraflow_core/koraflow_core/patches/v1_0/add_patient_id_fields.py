"""
Add SA ID Number and Passport fields to Patient DocType
"""
import frappe


def execute():
	"""Add custom fields to Patient DocType for SA ID and Passport capture"""
	
	fields_to_add = [
		{
			"dt": "Patient",
			"fieldname": "custom_sa_id_number",
			"fieldtype": "Data",
			"label": "South African ID Number",
			"description": "13-digit South African Identity Number",
			"insert_after": "sex",
			"in_standard_filter": 1,
			"translatable": 0
		},
		{
			"dt": "Patient",
			"fieldname": "custom_passport_number",
			"fieldtype": "Data",
			"label": "Passport Number",
			"description": "Passport number (if no SA ID)",
			"insert_after": "custom_sa_id_number",
			"translatable": 0
		},
		{
			"dt": "Patient",
			"fieldname": "custom_passport_country",
			"fieldtype": "Link",
			"label": "Passport Country",
			"options": "Country",
			"description": "Country that issued the passport",
			"insert_after": "custom_passport_number",
			"translatable": 0
		}
	]
	
	for field in fields_to_add:
		# Check if custom field already exists
		if frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
			print(f"Custom field {field['fieldname']} already exists on {field['dt']}")
			continue
		
		# Create custom field
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			**field
		})
		
		custom_field.insert(ignore_permissions=True)
		print(f"Added custom field {field['fieldname']} to {field['dt']}")
	
	frappe.db.commit()
	print("Patient ID fields patch completed")
