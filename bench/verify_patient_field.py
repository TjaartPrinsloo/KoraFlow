#!/usr/bin/env python3
"""Verify Sales Invoice patient field exists"""
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
    print("Verifying Sales Invoice patient field...")
    print("=" * 50)
    
    # Check if custom field exists
    custom_field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "patient"})
    print(f"Custom Field exists: {custom_field_exists}")
    
    # Check if database column exists
    try:
        result = frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE 'patient'", as_dict=True)
        column_exists = len(result) > 0
        print(f"Database column exists: {column_exists}")
        
        if not column_exists:
            print("\n⚠ Database column missing. Running schema update...")
            frappe.reload_doctype('Sales Invoice')
            frappe.db.commit()
            print("✓ Schema updated")
            
            # Verify again
            result = frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE 'patient'", as_dict=True)
            if len(result) > 0:
                print("✓ Database column now exists")
            else:
                print("✗ Database column still missing - may need full migrate")
        else:
            print("✓ All checks passed!")
            
    except Exception as e:
        print(f"Error checking column: {e}")
        print("Attempting schema update...")
        frappe.reload_doctype('Sales Invoice')
        frappe.db.commit()
        print("✓ Schema update completed")
    
    print("=" * 50)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.db.commit()
    frappe.destroy()
