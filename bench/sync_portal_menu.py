#!/usr/bin/env python3
"""
Sync portal menu items from hooks
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Syncing portal menu items...")
    
    # Get or create Portal Settings
    if frappe.db.exists("Portal Settings", "Portal Settings"):
        portal_settings = frappe.get_doc("Portal Settings", "Portal Settings")
    else:
        portal_settings = frappe.get_doc({
            "doctype": "Portal Settings",
            "name": "Portal Settings"
        })
        portal_settings.flags.ignore_permissions = True
        portal_settings.insert()
    
    # Sync menu from hooks
    portal_settings.sync_menu()
    frappe.db.commit()
    
    print("✓ Portal menu synced")
    print()
    print("Menu items:")
    for item in portal_settings.menu:
        if item.enabled:
            print(f"  - {item.title} ({item.route}) - Role: {item.role}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

