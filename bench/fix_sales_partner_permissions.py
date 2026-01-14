#!/usr/bin/env python3
"""
Fix Sales Partner Portal Role Permissions

This script:
1. Grants Read permission to Sales Partner Portal role for Sales Partner Referral
2. Grants Read + Create permission for Sales Partner Query
3. Verifies permission_query_conditions hooks are registered
4. Verifies User Permissions are set up correctly
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')

import frappe

ROLE_NAME = "Sales Partner Portal"


def fix_sales_partner_referral_permissions():
    """Fix permissions for Sales Partner Referral DocType"""
    print("Fixing Sales Partner Referral permissions...")
    
    if not frappe.db.exists("DocType", "Sales Partner Referral"):
        print("  ✗ Sales Partner Referral DocType does not exist")
        return False
    
    # Check if permission already exists
    existing = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "Sales Partner Referral",
            "role": ROLE_NAME
        },
        limit=1
    )
    
    if existing:
        print("  ✓ Permission already exists, updating...")
        perm = frappe.get_doc("Custom DocPerm", existing[0].name)
    else:
        print("  Creating new permission...")
        perm = frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": "Sales Partner Referral",
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": ROLE_NAME
        })
    
    # Set permissions (read only)
    perm.read = 1
    perm.write = 0
    perm.create = 0
    perm.delete = 0
    perm.submit = 0
    perm.cancel = 0
    perm.amend = 0
    perm.report = 0
    perm.print = 0
    perm.email = 0
    perm.export = 0
    
    perm.flags.ignore_permissions = True
    perm.save()
    frappe.db.commit()
    
    print("  ✓ Sales Partner Referral permissions updated")
    return True


def fix_sales_partner_query_permissions():
    """Fix permissions for Sales Partner Query DocType"""
    print("Fixing Sales Partner Query permissions...")
    
    if not frappe.db.exists("DocType", "Sales Partner Query"):
        print("  ✗ Sales Partner Query DocType does not exist")
        return False
    
    # Check if permission already exists
    existing = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "Sales Partner Query",
            "role": ROLE_NAME
        },
        limit=1
    )
    
    if existing:
        print("  ✓ Permission already exists, updating...")
        perm = frappe.get_doc("Custom DocPerm", existing[0].name)
    else:
        print("  Creating new permission...")
        perm = frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": "Sales Partner Query",
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": ROLE_NAME
        })
    
    # Set permissions (read + create)
    perm.read = 1
    perm.write = 0  # They can't edit, only create new queries
    perm.create = 1
    perm.delete = 0
    perm.submit = 0
    perm.cancel = 0
    perm.amend = 0
    perm.report = 0
    perm.print = 0
    perm.email = 0
    perm.export = 0
    
    perm.flags.ignore_permissions = True
    perm.save()
    frappe.db.commit()
    
    print("  ✓ Sales Partner Query permissions updated")
    return True


def verify_permission_query_conditions_hooks():
    """Verify permission_query_conditions hooks are registered"""
    print("Verifying permission_query_conditions hooks...")
    
    hooks = frappe.get_hooks("permission_query_conditions")
    
    required_hooks = {
        "Sales Partner Referral": "koraflow_core.doctype.sales_partner_referral.sales_partner_referral.get_permission_query_conditions",
        "Sales Partner Query": "koraflow_core.doctype.sales_partner_query.sales_partner_query.get_permission_query_conditions"
    }
    
    all_present = True
    for doctype, hook_path in required_hooks.items():
        if doctype in hooks:
            hook_value = hooks[doctype]
            if hook_path in hook_value or hook_path == hook_value:
                print(f"  ✓ {doctype} hook registered: {hook_path}")
            else:
                print(f"  ⚠ {doctype} hook registered but path differs: {hook_value}")
        else:
            print(f"  ✗ {doctype} hook NOT registered")
            all_present = False
    
    return all_present


def verify_user_permissions():
    """Verify User Permissions are set up for Sales Partner Portal users"""
    print("Verifying User Permissions...")
    
    # Get all Sales Partner Portal users
    users = frappe.get_all(
        "User",
        filters={
            "enabled": 1,
            "user_type": "Website User"
        },
        fields=["name", "full_name"]
    )
    
    sales_partner_users = []
    for user in users:
        roles = frappe.get_roles(user.name)
        if ROLE_NAME in roles:
            sales_partner_users.append(user)
    
    print(f"  Found {len(sales_partner_users)} Sales Partner Portal users")
    
    users_with_perms = 0
    users_without_perms = []
    
    for user in sales_partner_users:
        perms = frappe.get_all(
            "User Permission",
            filters={
                "user": user.name,
                "allow": "Sales Partner"
            },
            limit=1
        )
        
        if perms:
            users_with_perms += 1
        else:
            users_without_perms.append(user.name)
    
    print(f"  ✓ {users_with_perms} users have User Permissions")
    
    if users_without_perms:
        print(f"  ⚠ {len(users_without_perms)} users missing User Permissions:")
        for user in users_without_perms[:5]:  # Show first 5
            print(f"    - {user}")
        if len(users_without_perms) > 5:
            print(f"    ... and {len(users_without_perms) - 5} more")
    
    return len(users_without_perms) == 0


def main():
    """Main function"""
    frappe.init(site='koraflow-site', sites_path='sites')
    frappe.connect()
    
    print("=" * 60)
    print("Fixing Sales Partner Portal Permissions")
    print("=" * 60)
    print()
    
    # Fix permissions
    fix_sales_partner_referral_permissions()
    print()
    
    fix_sales_partner_query_permissions()
    print()
    
    # Verify hooks
    verify_permission_query_conditions_hooks()
    print()
    
    # Verify User Permissions
    verify_user_permissions()
    print()
    
    print("=" * 60)
    print("✓ Permissions fix complete")
    print("=" * 60)
    
    frappe.destroy()


if __name__ == "__main__":
    main()

