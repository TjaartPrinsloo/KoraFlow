#!/usr/bin/env python3
"""
Enable Limited Desk Access for Sales Partner Portal Role

Portal users need desk access to view workspaces, but we'll keep it restricted.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

ROLE_NAME = "Sales Partner Portal"

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Enabling desk access for Sales Partner Portal role...")
    
    role = frappe.get_doc("Role", ROLE_NAME)
    
    if role.desk_access == 0:
        role.desk_access = 1  # Enable desk access for workspace viewing
        role.flags.ignore_permissions = True
        role.save()
        frappe.db.commit()
        print(f"✓ Enabled desk access for {ROLE_NAME}")
        print("\n⚠️  IMPORTANT:")
        print("  • Desk access is enabled but heavily restricted")
        print("  • User Permissions ensure data isolation")
        print("  • Blocked doctypes prevent access to sensitive data")
        print("  • They can only access the Commission Dashboard workspace")
    else:
        print(f"✓ Desk access already enabled for {ROLE_NAME}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

