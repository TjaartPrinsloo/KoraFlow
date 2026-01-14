#!/usr/bin/env python3
"""
Remove Sales Partner Dashboard Workspace
Deletes the Sales Partner Dashboard workspace from the database.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

WORKSPACE_NAME = "Sales Partner Dashboard"


def remove_workspace():
    """Remove Sales Partner Dashboard workspace"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("REMOVING SALES PARTNER DASHBOARD")
        print("=" * 80)
        print()
        
        # Check if workspace exists
        if frappe.db.exists("Workspace", WORKSPACE_NAME):
            workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
            print(f"  Found workspace: {WORKSPACE_NAME}")
            print(f"  Title: {workspace.title}")
            print(f"  Module: {workspace.module}")
            
            # Delete the workspace
            frappe.delete_doc("Workspace", WORKSPACE_NAME, force=1)
            frappe.db.commit()
            print(f"  ✓ Deleted workspace: {WORKSPACE_NAME}")
        else:
            print(f"  ℹ Workspace '{WORKSPACE_NAME}' not found in database")
        
        # Also check for any workspaces with similar names
        similar_workspaces = frappe.get_all(
            "Workspace",
            filters={"title": ["like", "%Sales Partner%"]},
            fields=["name", "title"]
        )
        
        if similar_workspaces:
            print()
            print("  Found similar workspaces:")
            for ws in similar_workspaces:
                print(f"    - {ws.name} ({ws.title})")
            print()
            response = input("  Delete these as well? (y/n): ")
            if response.lower() == 'y':
                for ws in similar_workspaces:
                    frappe.delete_doc("Workspace", ws.name, force=1)
                    print(f"  ✓ Deleted: {ws.name}")
                frappe.db.commit()
        
        print()
        print("=" * 80)
        print("✅ REMOVAL COMPLETE")
        print("=" * 80)
        print()
        print("Note: You may need to clear browser cache or refresh the page")
        print("      to see the changes reflected in the UI.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Error removing workspace: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    remove_workspace()

