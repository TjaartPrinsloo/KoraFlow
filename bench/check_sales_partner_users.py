#!/usr/bin/env python3
"""
Check Sales Partner Users Configuration
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
    print("Checking sales partner users...")
    print()
    
    # Check the specific user that's logged in
    test_user = "anke.balt@koraflow.com"
    if frappe.db.exists("User", test_user):
        user = frappe.get_doc("User", test_user)
        print(f"User: {user.name}")
        print(f"  User Type: {user.user_type}")
        print(f"  Enabled: {user.enabled}")
        print(f"  Roles: {frappe.get_roles(user.name)}")
        print(f"  Default Workspace: {user.default_workspace}")
        
        if ROLE_NAME in frappe.get_roles(user.name):
            print(f"\n  ✓ User has {ROLE_NAME} role")
            if user.default_workspace != WORKSPACE_NAME:
                user.default_workspace = WORKSPACE_NAME
                user.flags.ignore_permissions = True
                user.save()
                frappe.db.commit()
                print(f"  ✓ Set default workspace to {WORKSPACE_NAME}")
            else:
                print(f"  ✓ Default workspace already set correctly")
        else:
            print(f"\n  ❌ User does NOT have {ROLE_NAME} role!")
    else:
        print(f"User {test_user} not found")
    
    print()
    
    # Find all users with Sales Partner Portal role
    all_users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "user_type", "default_workspace"])
    sp_users = []
    for user in all_users:
        roles = frappe.get_roles(user.name)
        if ROLE_NAME in roles:
            sp_users.append({
                "name": user.name,
                "user_type": user.user_type,
                "default_workspace": user.default_workspace,
                "roles": roles
            })
    
    print(f"Found {len(sp_users)} users with {ROLE_NAME} role:")
    for user in sp_users[:10]:  # Show first 10
        print(f"  • {user['name']}: {user['user_type']}, default_workspace: {user['default_workspace']}")
    
    if len(sp_users) > 10:
        print(f"  ... and {len(sp_users) - 10} more")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

