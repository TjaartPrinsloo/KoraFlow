#!/usr/bin/env python3
"""Run the fix for Sales Invoice patient field"""
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
    print("Fixing Sales Invoice patient field...")
    print("=" * 50)
    
    # Import and run the fix
    sys.path.insert(0, bench_dir)
    from fix_sales_invoice_patient_field import execute
    
    execute()
    
    print("=" * 50)
    print("✓ Fix completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.db.commit()
    frappe.destroy()
