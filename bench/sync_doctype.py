#!/usr/bin/env python3
"""Sync GLP-1 Intake Form DocType"""
import sys
import os

# Change to bench directory
bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

# Add apps to path
apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

# Change to sites directory for frappe.init
sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe

# Initialize and connect
frappe.init(site='koraflow-site')
frappe.connect()

try:
    # Check if DocType exists
    dt = frappe.db.get_value('DocType', 'GLP-1 Intake Form', 'name')
    print(f"DocType exists: {bool(dt)}")
    
    if not dt:
        print("Syncing GLP-1 Intake Form DocType...")
        frappe.reload_doc('koraflow_core', 'doctype', 'glp1_intake_form')
        frappe.db.commit()
        print("✓ DocType synced successfully")
    else:
        print("✓ DocType already exists")
    
    # Now run the patch
    print("\nRunning patch to add custom field...")
    from koraflow_core.koraflow_core.patches.v1_0.add_glp1_intake_field_to_patient import execute
    execute()
    frappe.db.commit()
    
    # Verify
    cf = frappe.db.get_value('Custom Field', {'dt': 'Patient', 'fieldname': 'glp1_intake_forms'}, ['name', 'label', 'fieldtype'], as_dict=True)
    if cf:
        print(f"✓ Custom Field created: {cf.name} ({cf.label}, {cf.fieldtype})")
    else:
        print("⚠ Custom field not found after creation")
    
except Exception as e:
    frappe.db.rollback()
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

