#!/usr/bin/env python3
"""
Remove Sales Partner Dashboard Portal Page
Removes the Web Page and portal menu item for sales-partner-dashboard.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

PAGE_NAME = "sales-partner-dashboard"
MENU_TITLE = "Commission Dashboard"


def remove_portal_page():
    """Remove Web Page and portal menu item"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("REMOVING SALES PARTNER PORTAL PAGE")
        print("=" * 80)
        print()
        
        # Remove Web Page
        if frappe.db.exists("Web Page", PAGE_NAME):
            page = frappe.get_doc("Web Page", PAGE_NAME)
            print(f"  Found Web Page: {PAGE_NAME}")
            print(f"  Title: {page.title}")
            print(f"  Route: {page.route}")
            
            frappe.delete_doc("Web Page", PAGE_NAME, force=1)
            frappe.db.commit()
            print(f"  ✓ Deleted Web Page: {PAGE_NAME}")
        else:
            print(f"  ℹ Web Page '{PAGE_NAME}' not found in database")
        
        # Remove portal menu item
        portal_settings = frappe.get_single("Portal Settings")
        menu_items_to_remove = []
        
        for item in portal_settings.menu:
            if item.route == f"/{PAGE_NAME}" or item.title == MENU_TITLE:
                menu_items_to_remove.append(item)
        
        if menu_items_to_remove:
            print()
            print(f"  Found {len(menu_items_to_remove)} portal menu item(s) to remove:")
            for item in menu_items_to_remove:
                print(f"    - {item.title} ({item.route})")
            
            # Remove menu items
            for item in menu_items_to_remove:
                portal_settings.remove(item)
            
            portal_settings.flags.ignore_permissions = True
            portal_settings.save()
            frappe.db.commit()
            print(f"  ✓ Removed {len(menu_items_to_remove)} portal menu item(s)")
        else:
            print(f"  ℹ No portal menu items found for '{PAGE_NAME}' or '{MENU_TITLE}'")
        
        print()
        print("=" * 80)
        print("✅ REMOVAL COMPLETE")
        print("=" * 80)
        print()
        print("Removed:")
        print(f"  • Web Page: {PAGE_NAME}")
        print(f"  • Portal menu items referencing this route")
        print()
        print("Note: Clear browser cache and refresh to see changes.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Error removing portal page: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    remove_portal_page()

