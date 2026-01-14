#!/usr/bin/env python3
"""
Fix missing patient field in Sales Invoice
This script ensures the patient custom field exists for Sales Invoice
as required by the Healthcare app.

Usage:
    bench --site [site] console
    Then: exec(open('fix_sales_invoice_patient_field.py').read())
    
Or run directly:
    bench --site [site] execute fix_sales_invoice_patient_field.execute
"""

import frappe


def execute():
	"""Ensure patient field exists in Sales Invoice"""
	
	# Check if custom field already exists
	if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "patient"}):
		print("✓ Custom field 'patient' already exists for Sales Invoice")
		# Still check if the database column exists
		try:
			frappe.db.sql("SELECT patient FROM `tabSales Invoice` LIMIT 1")
			print("✓ Database column 'patient' exists in tabSales Invoice")
			return
		except Exception as e:
			if frappe.db.is_missing_column(e):
				print("⚠ Custom field exists but database column is missing. Running migrate...")
				# The field exists in metadata but not in DB - need to migrate
				print("  Please run: bench --site [site] migrate")
				return
	
	# Create the custom field
	print("Creating custom field 'patient' for Sales Invoice...")
	
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	
	custom_fields = {
		"Sales Invoice": [
			{
				"fieldname": "patient",
				"label": "Patient",
				"fieldtype": "Link",
				"options": "Patient",
				"insert_after": "naming_series",
			},
			{
				"fieldname": "patient_name",
				"label": "Patient Name",
				"fieldtype": "Data",
				"fetch_from": "patient.patient_name",
				"insert_after": "patient",
				"read_only": True,
			},
		]
	}
	
	create_custom_fields(custom_fields, ignore_validate=True, update=True)
	frappe.db.commit()
	
	print("✓ Successfully created patient field for Sales Invoice")
	print("  Running migrate to create database column...")
	
	# Try to migrate to create the column
	try:
		from frappe.model.meta import trim_tables
		# This will trigger a schema update
		frappe.reload_doctype("Sales Invoice")
		frappe.db.commit()
		print("✓ Database column created successfully")
	except Exception as e:
		print(f"⚠ Could not auto-migrate: {e}")
		print("  Please run: bench --site [site] migrate")
	
	print("  Note: You may need to refresh your browser to see the changes")


if __name__ == "__main__":
	# This script should be run via bench console
	# bench --site <site> console
	# Then: exec(open('fix_sales_invoice_patient_field.py').read())
	execute()
