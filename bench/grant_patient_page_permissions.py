#!/usr/bin/env python3
"""
Grant Patient role permission to access Page doctype
This is required for patients to access web forms
"""

import frappe

def execute():
	"""Grant Patient role read permission on Page doctype"""
	
	# Check if Patient role exists
	if not frappe.db.exists("Role", "Patient"):
		print("Patient role does not exist. Creating it...")
		patient_role = frappe.get_doc({
			"doctype": "Role",
			"role_name": "Patient",
			"desk_access": 0
		})
		patient_role.insert(ignore_permissions=True)
		frappe.db.commit()
		print("✓ Patient role created")
	
	# Check if permission already exists
	existing_permission = frappe.db.get_value(
		"DocPerm",
		{
			"parent": "Page",
			"role": "Patient",
			"read": 1
		},
		"name"
	)
	
	if existing_permission:
		print("✓ Patient role already has read permission on Page doctype")
		return
	
	# Get Page doctype
	page_doctype = frappe.get_doc("DocType", "Page")
	
	# Add permission for Patient role
	page_doctype.append("permissions", {
		"role": "Patient",
		"read": 1,
		"create": 0,
		"write": 0,
		"delete": 0,
		"submit": 0,
		"cancel": 0,
		"amend": 0
	})
	
	page_doctype.save(ignore_permissions=True)
	frappe.db.commit()
	
	print("✓ Granted Patient role read permission on Page doctype")
	print("✓ Patients can now access web forms")

if __name__ == "__main__":
	import sys
	import os
	
	bench_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(bench_dir)
	sys.path.insert(0, 'apps')
	os.chdir('sites')
	
	# Get site name from sites directory
	sites = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('_')]
	if not sites:
		print("No sites found!")
		sys.exit(1)
	
	site_name = sites[0]
	print(f"Using site: {site_name}")
	
	frappe.init(site=site_name)
	frappe.connect()
	execute()
	frappe.db.close()
