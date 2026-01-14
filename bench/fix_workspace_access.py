#!/usr/bin/env python3
"""
Fix Workspace Access - Ensure workspace is properly registered and accessible
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

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Fixing workspace access...")
    print()
    
    ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    print(f"Workspace: {ws.name}")
    print(f"Title: {ws.title}")
    print(f"Public: {ws.public}")
    print(f"Is Hidden: {ws.is_hidden}")
    print()
    
    # Ensure workspace is public and not hidden
    if ws.is_hidden:
        ws.is_hidden = 0
        ws.flags.ignore_permissions = True
        ws.save()
        print("✓ Set workspace to not hidden")
    
    if not ws.public:
        ws.public = 1
        ws.flags.ignore_permissions = True
        ws.save()
        print("✓ Set workspace to public")
    
    # Ensure role is assigned
    roles = [r.role for r in ws.roles]
    if ROLE_NAME not in roles:
        ws.append("roles", {"role": ROLE_NAME})
        ws.flags.ignore_permissions = True
        ws.save()
        print(f"✓ Added {ROLE_NAME} role")
    
    frappe.db.commit()
    
    # Clear cache to ensure workspace is reloaded
    frappe.clear_cache()
    print("✓ Cleared cache")
    
    print()
    print("Workspace should now be accessible at:")
    print(f"  /app/commission-dashboard")
    print(f"  /app/sales-partner-dashboard")
    print()
    print("Note: User may need to refresh the page or log out/in for changes to take effect.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

