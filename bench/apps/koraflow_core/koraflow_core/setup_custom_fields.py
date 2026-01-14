# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Setup Custom Fields for Healthcare Dispensing
Adds prescription and patient fields to Stock Entry
"""

import frappe


def setup_custom_fields():
	"""Add custom fields to Stock Entry for prescription and patient references"""
	
	# Custom field for prescription
	if not frappe.db.exists("Custom Field", {"dt": "Stock Entry", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Stock Entry",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "reference_name",
			"description": "Link to GLP-1 Patient Prescription (required for S4 medications)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Stock Entry.custom_prescription")
	
	# Custom field for patient
	if not frappe.db.exists("Custom Field", {"dt": "Stock Entry", "fieldname": "custom_patient"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Stock Entry",
			"fieldname": "custom_patient",
			"label": "Patient",
			"fieldtype": "Link",
			"options": "Patient",
			"insert_after": "custom_prescription",
			"description": "Patient reference (required for S4 medications - anti-wholesaling compliance)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Stock Entry.custom_patient")
	
	# Custom field for prescription on Quotation
	if not frappe.db.exists("Custom Field", {"dt": "Quotation", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Quotation",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "party_name",
			"description": "Link to GLP-1 Patient Prescription"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Quotation.custom_prescription")
	
	# Custom field for prescription on Sales Order Item
	if not frappe.db.exists("Custom Field", {"dt": "Sales Order Item", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Order Item",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "item_code",
			"description": "Link to GLP-1 Patient Prescription (required for S4 medications)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Order Item.custom_prescription")
	
	# Custom field for prescription on Sales Invoice Item
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice Item", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice Item",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "item_code",
			"description": "Link to GLP-1 Patient Prescription (required for S4 medications)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice Item.custom_prescription")
	
	frappe.db.commit()
	frappe.msgprint("Custom fields setup completed")


if __name__ == "__main__":
	setup_custom_fields()
