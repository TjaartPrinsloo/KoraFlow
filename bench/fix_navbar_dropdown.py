#!/usr/bin/env python3
"""
Fix empty navbar dropdown by adding standard navbar items
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
    navbar_settings = frappe.get_single("Navbar Settings")
    
    print("Current Navbar Settings:")
    print(f"  Settings dropdown items: {len(navbar_settings.settings_dropdown) if navbar_settings.settings_dropdown else 0}")
    print(f"  Help dropdown items: {len(navbar_settings.help_dropdown) if navbar_settings.help_dropdown else 0}")
    
    if navbar_settings.settings_dropdown:
        print("\nCurrent settings dropdown items:")
        for item in navbar_settings.settings_dropdown:
            print(f"  - {item.item_label} ({item.item_type})")
    
    # Check if we need to add standard items
    if not navbar_settings.settings_dropdown or not navbar_settings.help_dropdown:
        print("\n⚠️  Navbar dropdown is empty. Adding standard items...")
        
        navbar_settings.settings_dropdown = []
        navbar_settings.help_dropdown = []
        
        for item in frappe.get_hooks("standard_navbar_items"):
            navbar_settings.append("settings_dropdown", item)
        
        for item in frappe.get_hooks("standard_help_items"):
            navbar_settings.append("help_dropdown", item)
        
        navbar_settings.save()
        frappe.db.commit()
        
        print("✅ Standard navbar items added successfully!")
        print(f"  Settings dropdown items: {len(navbar_settings.settings_dropdown)}")
        print(f"  Help dropdown items: {len(navbar_settings.help_dropdown)}")
    else:
        print("\n✅ Navbar dropdown already has items. No action needed.")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

