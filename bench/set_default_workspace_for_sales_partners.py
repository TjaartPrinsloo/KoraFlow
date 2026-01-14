#!/usr/bin/env python3
"""
Set Sales Partner Dashboard as Default Workspace for Sales Partner Users

This sets the default_workspace field on all users with the Sales Partner Portal role
to "Sales Partner Dashboard", so it appears as their default dashboard/home page.
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

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Sales Partner Dashboard"

try:
    print(f'Setting default workspace to "{WORKSPACE_NAME}" for all {ROLE_NAME} users...')
    print()
    
    # Verify workspace exists
    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        print(f'❌ Workspace "{WORKSPACE_NAME}" does not exist!')
        exit(1)
    
    # Find all users with Sales Partner Portal role
    all_users = frappe.get_all("User", 
        filters={"enabled": 1}, 
        fields=["name", "user_type", "default_workspace"]
    )
    
    sp_users = []
    for user in all_users:
        roles = frappe.get_roles(user.name)
        if ROLE_NAME in roles:
            sp_users.append(user)
    
    print(f'Found {len(sp_users)} users with {ROLE_NAME} role')
    print()
    
    updated = 0
    for user in sp_users:
        user_doc = frappe.get_doc("User", user.name)
        if user_doc.default_workspace != WORKSPACE_NAME:
            print(f'  Updating {user.name}:')
            print(f'    Old default_workspace: {user_doc.default_workspace or "None"}')
            user_doc.default_workspace = WORKSPACE_NAME
            user_doc.flags.ignore_permissions = True
            user_doc.save()
            updated += 1
            print(f'    ✓ Set to "{WORKSPACE_NAME}"')
        else:
            print(f'  ✓ {user.name} already has correct default workspace')
    
    if updated > 0:
        frappe.db.commit()
        print()
        print(f'✓ Updated {updated} users')
    else:
        print()
        print('✓ All users already have correct default workspace')
    
    print()
    print('Next steps:')
    print('  - Sales partners should log out and log back in')
    print('  - They will see "Sales Partner Dashboard" as their default workspace')
    print('  - It will appear in place of the default dashboard/home page')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

