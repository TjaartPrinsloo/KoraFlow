#!/usr/bin/env python3
"""
Debug Workspace Permission Check

Check why the workspace isn't being included in sidebar items.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.desk.desktop import Workspace

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Commission Dashboard"
TEST_USER = "anke.balt@koraflow.com"

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("=" * 80)
    print("DEBUGGING WORKSPACE PERMISSION")
    print("=" * 80)
    print()
    
    frappe.set_user(TEST_USER)
    print(f"User: {TEST_USER}")
    print(f"Roles: {frappe.get_roles()}")
    print()
    
    # Get workspace
    ws_doc = frappe.get_doc("Workspace", WORKSPACE_NAME)
    print(f"Workspace: {ws_doc.name}")
    print(f"Title: {ws_doc.title}")
    print(f"Public: {ws_doc.public}")
    print(f"Is Hidden: {ws_doc.is_hidden}")
    print(f"Module: {ws_doc.module}")
    print()
    
    # Check roles
    roles = [r.role for r in ws_doc.roles]
    print(f"Workspace roles: {roles}")
    print()
    
    # Check permission using Workspace class
    workspace = Workspace(ws_doc.as_dict(), True)
    
    print("Checking workspace.is_permitted()...")
    try:
        is_permitted = workspace.is_permitted()
        print(f"  Result: {is_permitted}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Check module blocking
    user_doc = frappe.get_cached_doc("User", TEST_USER)
    blocked_modules = user_doc.get_blocked_modules()
    print(f"Blocked modules: {blocked_modules}")
    if ws_doc.module in blocked_modules:
        print(f"  ⚠️  Workspace module '{ws_doc.module}' is blocked!")
    else:
        print(f"  ✓ Workspace module '{ws_doc.module}' is not blocked")
    
    print()
    
    # Check domain restrictions
    allowed_domains = [None, *frappe.get_active_domains()]
    print(f"Allowed domains: {allowed_domains}")
    print(f"Workspace restrict_to_domain: {ws_doc.restrict_to_domain}")
    if ws_doc.restrict_to_domain and ws_doc.restrict_to_domain not in allowed_domains:
        print(f"  ⚠️  Workspace domain '{ws_doc.restrict_to_domain}' not in allowed domains!")
    else:
        print(f"  ✓ Workspace domain is allowed")
    
    print()
    
    # Try to manually check if it would be included
    print("Manual check using get_workspace_sidebar_items logic...")
    from frappe.desk.desktop import get_workspace_sidebar_items
    
    sidebar_items = get_workspace_sidebar_items()
    pages = sidebar_items.get("pages", [])
    
    our_page = [p for p in pages if p.get("name") == WORKSPACE_NAME]
    if our_page:
        print(f"  ✓ Workspace IS in pages list!")
        print(f"  Page data: {our_page[0]}")
    else:
        print(f"  ❌ Workspace NOT in pages list")
        print()
        print("  Checking all workspaces that match filters...")
        filters = {
            "restrict_to_domain": ["in", allowed_domains],
            "module": ["not in", blocked_modules + ["Dummy Module"]],
        }
        all_workspaces = frappe.get_all(
            "Workspace",
            fields=["name", "title", "public", "is_hidden", "module", "restrict_to_domain"],
            filters=filters
        )
        our_ws_in_filter = [ws for ws in all_workspaces if ws.name == WORKSPACE_NAME]
        if our_ws_in_filter:
            print(f"  ✓ Workspace passes initial filters")
            print(f"  But might be filtered out by is_permitted() check")
        else:
            print(f"  ❌ Workspace doesn't pass initial filters!")
            print(f"  Check: module '{ws_doc.module}' in blocked? {ws_doc.module in blocked_modules}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

