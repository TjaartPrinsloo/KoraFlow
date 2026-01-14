#!/usr/bin/env python3
"""Create GLP-1 Intake Submission DocType"""
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
    doctype_path = os.path.join(bench_dir, 'apps', 'koraflow_core', 'koraflow_core', 'doctype', 'glp1_intake_submission', 'glp1_intake_submission.json')
    
    print(f"Reading DocType from: {doctype_path}")
    with open(doctype_path, 'r') as f:
        doctype_data = json.load(f)
    
    # Check if DocType exists
    dt_name = doctype_data.get('name', 'GLP-1 Intake Submission')
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
    
    # Now update the Web Form
    print("\nUpdating Web Form...")
    web_form_name = 'glp1-intake'
    web_form_exists = frappe.db.get_value('Web Form', web_form_name, 'name')
    
    if web_form_exists:
        web_form = frappe.get_doc('Web Form', web_form_name)
        web_form.doc_type = 'GLP-1 Intake Submission'
        web_form.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Web Form updated to use '{dt_name}' DocType")
    else:
        print(f"⚠ Web Form '{web_form_name}' not found - will be created when synced")
    
    print("\n" + "="*50)
    print("✓ SUCCESS: DocType created and Web Form updated!")
    print("="*50)
    
except Exception as e:
    frappe.db.rollback()
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

