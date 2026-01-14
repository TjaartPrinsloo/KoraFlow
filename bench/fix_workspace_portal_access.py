#!/usr/bin/env python3
"""
Fix Workspace Portal Access for Sales Partners

Portal users need Workspace read permissions to access workspaces.
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
    print("Checking Workspace permissions...")
    
    # Check if Workspace doctype has permissions for Sales Partner Portal role
    workspace_perms = frappe.get_all(
        "DocPerm",
        filters={"parent": "Workspace", "role": ROLE_NAME},
        fields=["read", "write"]
    )
    
    if not workspace_perms:
        print("  ⚠️  No Workspace permissions found for Sales Partner Portal role")
        print("  Creating read permission...")
        
        # Get Workspace doctype
        workspace_dt = frappe.get_doc("DocType", "Workspace")
        
        # Add permission
        workspace_dt.append("permissions", {
            "role": ROLE_NAME,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
            "report": 0,
            "export": 0,
            "print": 0,
            "email": 0,
            "share": 0,
        })
        
        workspace_dt.flags.ignore_permissions = True
        workspace_dt.save()
        frappe.db.commit()
        print("  ✓ Added Workspace read permission for Sales Partner Portal role")
    else:
        print(f"  ✓ Workspace permissions exist: {workspace_perms}")
    
    # Also check Number Card permissions
    number_card_perms = frappe.get_all(
        "DocPerm",
        filters={"parent": "Number Card", "role": ROLE_NAME},
        fields=["read"]
    )
    
    if not number_card_perms:
        print("  Creating Number Card read permission...")
        number_card_dt = frappe.get_doc("DocType", "Number Card")
        number_card_dt.append("permissions", {
            "role": ROLE_NAME,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
        })
        number_card_dt.flags.ignore_permissions = True
        number_card_dt.save()
        frappe.db.commit()
        print("  ✓ Added Number Card read permission")
    else:
        print(f"  ✓ Number Card permissions exist")
    
    print("\n✅ Permissions updated!")
    print("\nNote: Portal users may still need desk access enabled.")
    print("Consider setting default_workspace for sales partner users.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

