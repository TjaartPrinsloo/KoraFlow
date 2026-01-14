#!/usr/bin/env python3
"""
Verify Workspace Routing and Fix Access

Check workspace name, title, route slug, and set as default for sales partners.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.desk.utils import slug

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Commission Dashboard"

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("=" * 80)
    print("VERIFYING WORKSPACE ROUTING")
    print("=" * 80)
    print()
    
    # Get workspace
    ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    print(f"Workspace Name: {ws.name}")
    print(f"Title: {ws.title}")
    print(f"Public: {ws.public}")
    print()
    
    # Calculate route slugs
    name_slug = slug(ws.name.lower())
    title_slug = slug(ws.title.lower())
    
    print(f"Route slug from name: {name_slug}")
    print(f"Route slug from title: {title_slug}")
    print()
    
    # Check what routes should work
    print("Expected routes:")
    print(f"  /app/{name_slug}")
    print(f"  /app/{title_slug}")
    print()
    
    # Check roles
    roles = [r.role for r in ws.roles]
    print(f"Workspace roles: {roles}")
    if ROLE_NAME not in roles:
        print(f"  ⚠️  {ROLE_NAME} not in workspace roles!")
        ws.append("roles", {"role": ROLE_NAME})
        ws.flags.ignore_permissions = True
        ws.save()
        frappe.db.commit()
        print(f"  ✓ Added {ROLE_NAME} to workspace roles")
    else:
        print(f"  ✓ {ROLE_NAME} is in workspace roles")
    print()
    
    # Set as default workspace for sales partner users
    print("Setting default workspace for sales partner users...")
    sales_partner_users = frappe.get_all(
        "User",
        filters={"user_type": "Website User", "enabled": 1},
        fields=["name", "default_workspace"]
    )
    
    # Filter to only users with Sales Partner Portal role
    sp_users = []
    for user in sales_partner_users:
        user_roles = frappe.get_roles(user.name)
        if ROLE_NAME in user_roles:
            sp_users.append(user)
    
    print(f"Found {len(sp_users)} sales partner users")
    
    updated_count = 0
    for user in sp_users:
        if user.default_workspace != ws.name:
            user_doc = frappe.get_doc("User", user.name)
            user_doc.default_workspace = ws.name
            user_doc.flags.ignore_permissions = True
            user_doc.save()
            updated_count += 1
            print(f"  ✓ Set default workspace for {user.name}")
    
    if updated_count > 0:
        frappe.db.commit()
        print(f"\n✓ Updated default workspace for {updated_count} users")
    else:
        print("\n✓ All users already have correct default workspace")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Workspace: {ws.name}")
    print(f"Title: {ws.title}")
    print(f"Accessible via: /app/{name_slug} or /app/{title_slug}")
    print(f"Default workspace set for {len(sp_users)} sales partner users")
    print()
    print("Try accessing:")
    print(f"  http://localhost:8002/app/{name_slug}")
    print(f"  http://localhost:8002/app/{title_slug}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

