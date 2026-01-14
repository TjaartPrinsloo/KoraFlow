#!/usr/bin/env python3
"""
Fix Page Doctype Permissions for Sales Partner Portal Role

Sales partners need read access to the Page doctype to view workspaces.
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
    print("Adding Page doctype permissions for Sales Partner Portal role...")
    
    # Get Page doctype
    page_dt = frappe.get_doc("DocType", "Page")
    
    # Check if permission already exists
    existing = [p for p in page_dt.permissions if p.role == ROLE_NAME]
    
    if existing:
        print(f"  ✓ Page permissions already exist for {ROLE_NAME}")
        perm = existing[0]
        print(f"    Read: {perm.read}, Write: {perm.write}, Create: {perm.create}")
    else:
        # Add read-only permission
        page_dt.append("permissions", {
            "role": ROLE_NAME,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
            "report": 0,
            "export": 0,
            "print": 0,
            "email": 0,
            "share": 0,
        })
        
        page_dt.flags.ignore_permissions = True
        page_dt.save()
        frappe.db.commit()
        print(f"  ✓ Added Page read permission for {ROLE_NAME}")
    
    print("\n✅ Permissions updated!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

