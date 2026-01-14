#!/usr/bin/env python3
"""
Add Portal Menu Item for Sales Partner Dashboard
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
    # Get Portal Settings
    portal_settings = frappe.get_single("Portal Settings")
    
    # Check if menu item already exists
    existing = [item for item in portal_settings.menu if item.title == "Commission Dashboard"]
    
    if not existing:
        portal_settings.append("menu", {
            "title": "Commission Dashboard",
            "route": "/sales-partner-dashboard",
            "enabled": 1,
        })
        portal_settings.flags.ignore_permissions = True
        portal_settings.save()
        frappe.db.commit()
        print("✓ Added 'Commission Dashboard' to portal menu")
    else:
        print("✓ Portal menu item already exists")
    
    print("\nPortal menu items:")
    for item in portal_settings.menu:
        if item.enabled:
            print(f"  • {item.title}: {item.route}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

