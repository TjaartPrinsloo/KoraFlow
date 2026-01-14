#!/usr/bin/env python3
"""Run prescription setup: Add custom fields and import print format"""
import sys
import os
import json

# Change to bench directory
bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

# Add apps to path - need to add the actual frappe app
apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

# Also add frappe to path explicitly
frappe_path = os.path.join(apps_dir, 'frappe')
if os.path.exists(frappe_path):
    sys.path.insert(0, frappe_path)

# Change to sites directory for frappe.init
sites_dir = os.path.join(bench_dir, 'sites')
if not os.path.exists(sites_dir):
    print(f"Error: Sites directory not found at {sites_dir}")
    sys.exit(1)

os.chdir(sites_dir)

# Try to detect site name from sites directory
sites = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
if not sites:
    print("Error: No sites found in sites directory")
    sys.exit(1)

site_name = sites[0]  # Use first site found
print(f"Using site: {site_name}")

# Import frappe after setting up paths
try:
    import frappe
except ImportError as e:
    print(f"Error importing frappe: {e}")
    print(f"Python path: {sys.path}")
    print(f"Looking for frappe in: {apps_dir}")
    sys.exit(1)

# Initialize and connect
try:
    frappe.init(site=site_name)
    frappe.connect()
except Exception as e:
    print(f"Error initializing frappe: {e}")
    sys.exit(1)

try:
    # Step 1: Run the patch to add custom fields
    print("\n" + "="*60)
    print("Step 1: Adding custom fields to Healthcare Practitioner")
    print("="*60)
    
    from koraflow_core.koraflow_core.patches.v1_0.add_prescription_fields_to_practitioner import execute as execute_patch
    
    execute_patch()
    frappe.db.commit()
    
    # Verify the custom fields were created
    custom_fields = frappe.db.get_all('Custom Field', 
        filters={'dt': 'Healthcare Practitioner', 
                 'fieldname': ['in', ['practice_number', 'hpcsa_registration_number', 'prescription_template', 'prescription_print_format']]},
        fields=['name', 'fieldname', 'label', 'fieldtype'],
        as_dict=True)
    
    if custom_fields:
        print(f"✓ Patch executed successfully!")
        print(f"✓ Custom Fields created:")
        for cf in custom_fields:
            print(f"  - {cf.fieldname} ({cf.label}, {cf.fieldtype})")
    else:
        print("⚠ Patch executed but custom fields not found. They may already exist.")
    
    # Step 2: Import the print format
    print("\n" + "="*60)
    print("Step 2: Importing SAHPRA Prescription Print Format")
    print("="*60)
    
    print_format_path = os.path.join(bench_dir, 'apps', 'koraflow_core', 'koraflow_core', 'print_format', 'sahpra_prescription', 'sahpra_prescription.json')
    
    # Also try alternative path structure
    if not os.path.exists(print_format_path):
        alt_path = os.path.join(bench_dir, 'apps', 'koraflow_core', 'print_format', 'sahpra_prescription', 'sahpra_prescription.json')
        if os.path.exists(alt_path):
            print_format_path = alt_path
    
    if not os.path.exists(print_format_path):
        print(f"✗ Error: Print format file not found at {print_format_path}")
        sys.exit(1)
    
    with open(print_format_path, 'r') as f:
        print_format_data = json.load(f)
    
    # Check if print format already exists
    if frappe.db.exists("Print Format", print_format_data.get("name")):
        print(f"⚠ Print Format '{print_format_data.get('name')}' already exists. Updating...")
        existing_doc = frappe.get_doc("Print Format", print_format_data.get("name"))
        existing_doc.update(print_format_data)
        existing_doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Print Format updated successfully!")
    else:
        # Create new print format
        print_format_doc = frappe.get_doc(print_format_data)
        print_format_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Print Format '{print_format_data.get('name')}' created successfully!")
    
    print("\n" + "="*60)
    print("✓ Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Configure Healthcare Practitioners with practice details")
    print("2. Test by submitting a Patient Encounter with medications")
    print("3. Check Patient record attachments for generated prescription PDF")
    
except Exception as e:
    frappe.db.rollback()
    print(f"\n✗ Error during setup: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()
