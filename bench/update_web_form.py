#!/usr/bin/env python3
"""Update Web Form with all intake fields"""
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
    # Read the Web Form JSON file
    web_form_path = os.path.join(bench_dir, 'apps', 'koraflow_core', 'koraflow_core', 'web_form', 'glp1_intake', 'glp1_intake.json')
    
    print(f"Reading Web Form from: {web_form_path}")
    with open(web_form_path, 'r') as f:
        web_form_data = json.load(f)
    
    # Check if Web Form exists
    web_form_name = web_form_data.get('name', 'glp1-intake')
    existing = frappe.db.get_value('Web Form', web_form_name, 'name')
    
    # Check by route as well
    route = web_form_data.get('route', 'glp1-intake')
    existing_by_route = frappe.db.get_value('Web Form', {'route': route}, 'name')
    
    if existing or existing_by_route:
        web_form_name_to_use = existing or existing_by_route
        print(f"Updating Web Form '{web_form_name_to_use}'...")
        # Get the existing Web Form
        web_form = frappe.get_doc('Web Form', web_form_name_to_use)
        
        # Update doc_type first
        web_form.doc_type = web_form_data.get('doc_type', 'GLP-1 Intake Submission')
        
        # Update web_form_fields
        web_form.web_form_fields = []
        for field in web_form_data.get('web_form_fields', []):
            web_form.append('web_form_fields', field)
        
        # Update other fields
        web_form.title = web_form_data.get('title', web_form.title)
        web_form.introduction_text = web_form_data.get('introduction_text', web_form.introduction_text)
        web_form.button_label = web_form_data.get('button_label', web_form.button_label)
        web_form.success_message = web_form_data.get('success_message', web_form.success_message)
        web_form.success_url = web_form_data.get('success_url', web_form.success_url)
        web_form.is_standard = web_form_data.get('is_standard', 0)
        
        web_form.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Web Form '{web_form_name_to_use}' updated with {len(web_form_data.get('web_form_fields', []))} fields")
    else:
        print(f"Creating Web Form '{web_form_name}'...")
        # Create new Web Form
        web_form = frappe.get_doc(web_form_data)
        web_form.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✓ Web Form '{web_form_name}' created")
    
    # Verify
    field_count = frappe.db.get_value('Web Form', web_form_name, 
        frappe.db.count('Web Form Field', {'parent': web_form_name}))
    print(f"✓ Web Form now has fields in database")
    
except Exception as e:
    frappe.db.rollback()
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

