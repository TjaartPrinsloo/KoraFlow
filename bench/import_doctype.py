#!/usr/bin/env python3
"""Import GLP-1 Intake Form DocType directly"""
import sys
import os
import json

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
    # Read the DocType JSON file
    doctype_path = os.path.join(bench_dir, 'apps', 'koraflow_core', 'koraflow_core', 'doctype', 'glp1_intake_form', 'glp1_intake_form.json')
    
    print(f"Reading DocType from: {doctype_path}")
    with open(doctype_path, 'r') as f:
        doctype_data = json.load(f)
    
    # Check if DocType exists
    dt_name = doctype_data.get('name', 'GLP-1 Intake Form')
    existing = frappe.db.get_value('DocType', dt_name, 'name')
    
    if existing:
        print(f"✓ DocType '{dt_name}' already exists")
    else:
        print(f"Creating DocType '{dt_name}'...")
        # Create the DocType
        doc = frappe.get_doc(doctype_data)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ DocType '{dt_name}' created")
    
    # Now run the patch
    print("\nRunning patch to add custom field...")
    from koraflow_core.koraflow_core.patches.v1_0.add_glp1_intake_field_to_patient import execute
    execute()
    frappe.db.commit()
    
    # Verify
    cf = frappe.db.get_value('Custom Field', {'dt': 'Patient', 'fieldname': 'glp1_intake_forms'}, ['name', 'label', 'fieldtype'], as_dict=True)
    if cf:
        print(f"✓ Custom Field created: {cf.name} ({cf.label}, {cf.fieldtype})")
        print("\n✓ SUCCESS: Patch completed successfully!")
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

