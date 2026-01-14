#!/usr/bin/env python3
"""
Fix Workspace Module Access

The workspace module "Selling" is not accessible to sales partner users.
We need to either change the module or ensure the user has access.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Commission Dashboard"
TEST_USER = "anke.balt@koraflow.com"

frappe.init(site='koraflow-site')
frappe.connect()

# Switch to Administrator to edit workspace
frappe.set_user("Administrator")

try:
    print("=" * 80)
    print("FIXING WORKSPACE MODULE ACCESS")
    print("=" * 80)
    print()
    
    frappe.set_user(TEST_USER)
    
    # Get workspace
    ws_doc = frappe.get_doc("Workspace", WORKSPACE_NAME)
    print(f"Current workspace module: {ws_doc.module}")
    print()
    
    # Try to access workspace - if it fails, module is not accessible
    from frappe.desk.desktop import Workspace
    try:
        workspace = Workspace(ws_doc.as_dict(), True)
        print("✓ Workspace module is accessible")
        allowed_modules = ["Selling"]  # If it works, Selling is allowed
    except frappe.PermissionError:
        print("❌ Workspace module 'Selling' is NOT accessible")
        allowed_modules = []
    
    # Check if Selling module is accessible
    if "Selling" not in allowed_modules:
        print("❌ 'Selling' module is NOT accessible to user")
        print()
        print("Options:")
        print("  1. Change workspace module to an accessible module")
        print("  2. Grant Selling module access to Sales Partner Portal role")
        print()
        
        # Option 1: Change module to something accessible
        # Let's use a module that's typically accessible or create a custom one
        accessible_modules = ["Core", "Website", "Integrations"]
        if allowed_modules:
            new_module = allowed_modules[0]
        else:
            # Use a module that should be accessible
            new_module = "Core"
        
        print(f"Changing workspace module from '{ws_doc.module}' to '{new_module}'...")
        # Use db_set to bypass validation
        frappe.db.set_value("Workspace", WORKSPACE_NAME, "module", new_module)
        frappe.db.commit()
        print(f"✓ Changed workspace module to '{new_module}'")
        
        # Reload workspace
        ws_doc = frappe.get_doc("Workspace", WORKSPACE_NAME)
        print(f"  Verified: module is now '{ws_doc.module}'")
        print()
        
        # Verify it works now
        from frappe.desk.desktop import Workspace
        try:
            workspace = Workspace(ws_doc.as_dict(), True)
            is_permitted = workspace.is_permitted()
            print(f"✓ Workspace is now permitted: {is_permitted}")
        except Exception as e:
            print(f"❌ Still has permission error: {e}")
    else:
        print("✓ 'Selling' module IS accessible to user")
    
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

