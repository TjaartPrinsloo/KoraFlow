#!/usr/bin/env python3
"""
Check Boot Workspace List for Sales Partner User

Verify if the workspace is included in the user's boot data.
"""

import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.desk.desktop import get_workspace_sidebar_items

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Commission Dashboard"
TEST_USER = "anke.balt@koraflow.com"

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("=" * 80)
    print("CHECKING BOOT WORKSPACE LIST")
    print("=" * 80)
    print()
    
    # Switch to test user context
    frappe.set_user(TEST_USER)
    print(f"Checking for user: {TEST_USER}")
    print(f"User roles: {frappe.get_roles()}")
    print()
    
    # Get workspace sidebar items (this is what gets sent to client)
    sidebar_items = get_workspace_sidebar_items()
    
    print(f"Total workspace items: {len(sidebar_items)}")
    print()
    
    # Look for our workspace
    found_workspace = False
    print("Looking for 'Commission Dashboard' or 'Sales Partner Dashboard'...")
    print()
    
    for item in sidebar_items:
        if isinstance(item, dict):
            title = item.get('title', '')
            name = item.get('name', '')
            route = item.get('route', '')
            
            if WORKSPACE_NAME.lower() in title.lower() or WORKSPACE_NAME.lower() in name.lower():
                found_workspace = True
                print(f"✓ FOUND WORKSPACE:")
                print(f"  Title: {title}")
                print(f"  Name: {name}")
                print(f"  Route: {route}")
                print(f"  Type: {item.get('type', 'N/A')}")
                print(f"  Public: {item.get('public', 'N/A')}")
                print()
    
    if not found_workspace:
        print("❌ Workspace NOT found in sidebar items!")
        print()
        print(f"Sidebar items type: {type(sidebar_items)}")
        if isinstance(sidebar_items, dict):
            print(f"Sidebar items keys: {list(sidebar_items.keys())}")
            if 'pages' in sidebar_items:
                pages = sidebar_items['pages']
                print(f"Number of pages: {len(pages)}")
                print()
                print("Available workspaces:")
                for i, item in enumerate(pages[:20]):  # Show first 20
                    if isinstance(item, dict):
                        print(f"  {i+1}. {item.get('title', 'N/A')} ({item.get('name', 'N/A')})")
        elif isinstance(sidebar_items, (list, tuple)):
            print(f"Sidebar items is a list/tuple with {len(sidebar_items)} items")
            for i, item in enumerate(list(sidebar_items)[:20]):
                if isinstance(item, dict):
                    print(f"  {i+1}. {item.get('title', 'N/A')} ({item.get('name', 'N/A')})")
        print()
    
    # Also check directly via workspace query
    print("Checking workspace directly...")
    workspaces = frappe.get_all(
        "Workspace",
        filters={"public": 1},
        fields=["name", "title", "public", "is_hidden"]
    )
    
    our_workspace = [ws for ws in workspaces if ws.name == WORKSPACE_NAME or WORKSPACE_NAME.lower() in ws.title.lower()]
    
    if our_workspace:
        ws = our_workspace[0]
        print(f"✓ Workspace exists in database:")
        print(f"  Name: {ws.name}")
        print(f"  Title: {ws.title}")
        print(f"  Public: {ws.public}")
        print(f"  Is Hidden: {ws.is_hidden}")
        
        # Check roles
        ws_doc = frappe.get_doc("Workspace", ws.name)
        roles = [r.role for r in ws_doc.roles]
        print(f"  Roles: {roles}")
        
        if ROLE_NAME not in roles:
            print(f"  ⚠️  {ROLE_NAME} not in workspace roles!")
        else:
            print(f"  ✓ {ROLE_NAME} is in workspace roles")
    else:
        print(f"❌ Workspace '{WORKSPACE_NAME}' not found in database!")
    
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

