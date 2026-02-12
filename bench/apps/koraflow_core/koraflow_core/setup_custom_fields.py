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
	
	# Custom field for prescription on Sales Order
	if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "customer_address",
			"description": "Link to GLP-1 Patient Prescription (required for S4 medications)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Order.custom_prescription")
	
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
	
	# Custom field for service_unit on Sales Invoice (required by healthcare app)
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "service_unit"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice",
			"fieldname": "service_unit",
			"label": "Service Unit",
			"fieldtype": "Link",
			"options": "Healthcare Service Unit",
			"insert_after": "customer",
			"description": "Healthcare Service Unit (required for healthcare validation)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice.service_unit")
	
	# Custom field for prescription on Sales Invoice
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice",
			"fieldname": "custom_prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "service_unit",
			"description": "Link to GLP-1 Patient Prescription (required for S4 medications)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice.custom_prescription")
	
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
	
	# Custom field for reference_dt on Sales Invoice Item (required by healthcare app)
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice Item", "fieldname": "reference_dt"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice Item",
			"fieldname": "reference_dt",
			"label": "Reference Document Type",
			"fieldtype": "Link",
			"options": "DocType",
			"hidden": 1,
			"insert_after": "item_code",
			"description": "Reference Document Type (required by healthcare app)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice Item.reference_dt")
		
	# Custom field for reference_dn on Sales Invoice Item (required by healthcare app)
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice Item", "fieldname": "reference_dn"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice Item",
			"fieldname": "reference_dn",
			"label": "Reference Name",
			"fieldtype": "Data",
			"hidden": 1,
			"insert_after": "reference_dt",
			"description": "Reference Document Name (required by healthcare app)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice Item.reference_dn")
	
	# Custom field for valid_till on Quotation (for 48-hour quote validity)
	if not frappe.db.exists("Custom Field", {"dt": "Quotation", "fieldname": "custom_valid_until"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Quotation",
			"fieldname": "custom_valid_until",
			"label": "Quote Valid Until",
			"fieldtype": "Date",
			"insert_after": "custom_prescription",
			"description": "Quote validity date (auto-set to 48 hours from creation)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Quotation.custom_valid_until")
	
	# Custom fields for Xero integration on Sales Invoice
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_xero_invoice_id"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice",
			"fieldname": "custom_xero_invoice_id",
			"label": "Xero Invoice ID",
			"fieldtype": "Data",
			"insert_after": "naming_series",
			"read_only": 1,
			"description": "Xero Invoice ID for 2-way sync"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice.custom_xero_invoice_id")
	
	if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "custom_xero_voided"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Invoice",
			"fieldname": "custom_xero_voided",
			"label": "Voided in Xero",
			"fieldtype": "Check",
			"insert_after": "custom_xero_invoice_id",
			"read_only": 1,
			"description": "Invoice voided in Xero"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Sales Invoice.custom_xero_voided")
	
	# Custom fields for Pick List GLP-1 context
	if not frappe.db.exists("Custom Field", {"dt": "Pick List", "fieldname": "custom_glp1_prescription"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Pick List",
			"fieldname": "custom_glp1_prescription",
			"label": "GLP-1 Prescription",
			"fieldtype": "Link",
			"options": "GLP-1 Patient Prescription",
			"insert_after": "purpose",
			"read_only": 1,
			"description": "Linked GLP-1 Prescription for pharmacy context"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Pick List.custom_glp1_prescription")
	
	if not frappe.db.exists("Custom Field", {"dt": "Pick List", "fieldname": "custom_patient"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Pick List",
			"fieldname": "custom_patient",
			"label": "Patient",
			"fieldtype": "Link",
			"options": "Patient",
			"insert_after": "custom_glp1_prescription",
			"read_only": 1,
			"description": "Patient for pharmacy dispensing context"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.msgprint("Created custom field: Pick List.custom_patient")
	
	frappe.db.commit()
	frappe.msgprint("Custom fields setup completed")


def setup_item_schedule_field():
	"""Add custom field to Item for Schedule (S0-S5)"""
	if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "custom_schedule"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Item",
			"fieldname": "custom_schedule",
			"label": "Schedule",
			"fieldtype": "Select",
			"options": "S0\nS1\nS2\nS3\nS4\nS5",
			"insert_after": "item_group",
			"description": "Pharmaceutical Schedule (S4 requires prescription)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Created custom field: Item.custom_schedule")


def setup_medication_dispensing_field():
	"""Add custom field to Medication for in-house dispensing flag"""
	
	# Custom field for dispensed_in_house on Medication
	if not frappe.db.exists("Custom Field", {"dt": "Medication", "fieldname": "custom_dispensed_in_house"}):
		custom_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Medication",
			"fieldname": "custom_dispensed_in_house",
			"label": "Dispensed In-House",
			"fieldtype": "Check",
			"insert_after": "disabled",
			"description": "If checked, prescriptions for this medication will NOT be visible to patients (for S4 in-house dispensed items)"
		})
		custom_field.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Created custom field: Medication.custom_dispensed_in_house")
		return True
	else:
		frappe.msgprint("Custom field Medication.custom_dispensed_in_house already exists")
		return False


if __name__ == "__main__":
	setup_custom_fields()
	setup_item_schedule_field()
	setup_medication_dispensing_field()
