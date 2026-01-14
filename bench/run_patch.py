#!/usr/bin/env python3
"""Run the GLP-1 Intake Form patch"""
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

# Run the patch
from koraflow_core.koraflow_core.patches.v1_0.add_glp1_intake_field_to_patient import execute

try:
    print("Running patch: add_glp1_intake_field_to_patient")
    execute()
    frappe.db.commit()
    
    # Verify the custom field was created
    cf = frappe.db.get_value('Custom Field', {'dt': 'Patient', 'fieldname': 'glp1_intake_forms'}, ['name', 'label', 'fieldtype'], as_dict=True)
    if cf:
        print(f"✓ Patch executed successfully!")
        print(f"✓ Custom Field created: {cf.name} ({cf.label}, {cf.fieldtype})")
    else:
        print("⚠ Patch executed but custom field not found. It may already exist or there was an issue.")
    
except Exception as e:
    frappe.db.rollback()
    print(f"✗ Error running patch: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

