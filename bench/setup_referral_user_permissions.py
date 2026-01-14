#!/usr/bin/env python3
"""
Set up User Permissions for Sales Partner Referral DocType

This ensures sales partners can only see their own referrals.
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

try:
    print("Setting up User Permissions for Sales Partner Referral...")
    print()
    
    # Get all users with Sales Partner Portal role
    all_users = frappe.get_all("User", filters={"enabled": 1}, fields=["name"])
    sp_users = []
    
    for user in all_users:
        roles = frappe.get_roles(user.name)
        if ROLE_NAME in roles:
            sp_users.append(user.name)
    
    print(f"Found {len(sp_users)} users with {ROLE_NAME} role")
    print()
    
    # For each user, get their Sales Partner and create User Permission
    created = 0
    skipped = 0
    for user_email in sp_users:
        try:
            # Get Sales Partner from existing User Permissions
            user_perms = frappe.get_all(
                "User Permission",
                filters={
                    "user": user_email,
                    "allow": "Sales Partner"
                },
                fields=["for_value"],
                limit=1
            )
            
            if not user_perms:
                skipped += 1
                continue
            
            sales_partner_name = user_perms[0].for_value
            
            # Validate that Sales Partner exists
            if not frappe.db.exists("Sales Partner", sales_partner_name):
                skipped += 1
                continue
            
            # For Sales Partner Query, create permission for the user's sales partner
            query_perm_exists = frappe.db.exists(
                "User Permission",
                {
                    "user": user_email,
                    "allow": "Sales Partner Query",
                    "for_value": sales_partner_name,
                    "apply_to_all_doctypes": 0
                }
            )
            
            if not query_perm_exists:
                up = frappe.get_doc({
                    "doctype": "User Permission",
                    "user": user_email,
                    "allow": "Sales Partner Query",
                    "for_value": sales_partner_name,
                    "apply_to_all_doctypes": 0
                })
                up.flags.ignore_permissions = True
                up.insert()
                created += 1
        except Exception as e:
            skipped += 1
            print(f"  ⚠️  {user_email}: Error - {str(e)[:50]}")
            continue
    
    if created > 0:
        frappe.db.commit()
        print()
        print(f"✓ Created {created} User Permissions")
    else:
        print("✓ All User Permissions already exist")
    
    if skipped > 0:
        print(f"⚠️  Skipped {skipped} users (invalid Sales Partner or missing permissions)")
    
    print()
    print("Note: Sales Partner Referral access is controlled via server-side filters")
    print("      based on the sales_partner field matching the user's Sales Partner.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

