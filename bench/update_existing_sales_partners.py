#!/usr/bin/env python3
"""
Update Existing Sales Partner Users

This script updates existing sales partner users that were created before
the security setup. It:
1. Changes user_type from System User to Website User
2. Removes Sales User role
3. Adds Sales Partner Portal role
4. Ensures User Permissions are set up

Run with:
    python3 update_existing_sales_partners.py
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

ROLE_NAME = "Sales Partner Portal"


def update_sales_partner_users():
    """Update all existing sales partner users"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("UPDATING EXISTING SALES PARTNER USERS")
        print("=" * 80)
        print()
        
        # Find all users with Sales Partner User Permission
        user_permissions = frappe.get_all(
            "User Permission",
            filters={"allow": "Sales Partner"},
            fields=["user", "for_value"]
        )
        
        if not user_permissions:
            print("⚠️  No sales partner users found with User Permissions.")
            print("   Run create_sales_partners.py first to create users.")
            return
        
        updated = 0
        errors = []
        
        for up in user_permissions:
            user_email = up.user
            sales_partner_name = up.for_value
            
            try:
                if not frappe.db.exists("User", user_email):
                    print(f"⚠️  User not found: {user_email}")
                    continue
                
                user_doc = frappe.get_doc("User", user_email)
                roles = [r.role for r in user_doc.roles]
                
                changes_made = []
                
                # 1. Change user_type to Website User
                if user_doc.user_type != "Website User":
                    user_doc.user_type = "Website User"
                    changes_made.append("user_type → Website User")
                
                # 2. Remove Sales User role if present
                if "Sales User" in roles:
                    user_doc.remove_roles("Sales User")
                    changes_made.append("removed Sales User role")
                
                # 3. Add Sales Partner Portal role if not present
                if ROLE_NAME not in roles:
                    if frappe.db.exists("Role", ROLE_NAME):
                        user_doc.add_roles(ROLE_NAME)
                        changes_made.append(f"added {ROLE_NAME} role")
                    else:
                        errors.append(f"{user_email}: Role '{ROLE_NAME}' does not exist. Run setup_sales_partner_permissions.py first.")
                        print(f"❌ {user_email}: Role '{ROLE_NAME}' not found. Run setup_sales_partner_permissions.py first.")
                        continue
                
                # Save if changes were made
                if changes_made:
                    user_doc.flags.ignore_permissions = True
                    user_doc.save()
                    updated += 1
                    print(f"✓ Updated: {user_email} ({sales_partner_name})")
                    print(f"  Changes: {', '.join(changes_made)}")
                else:
                    print(f"✓ Already correct: {user_email} ({sales_partner_name})")
                
            except Exception as e:
                error_msg = f"Error updating {user_email}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                frappe.log_error(error_msg, f"Update Sales Partner User Error: {user_email}")
        
        frappe.db.commit()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total users found: {len(user_permissions)}")
        print(f"Updated: {updated}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print()
            print("Errors:")
            for error in errors:
                print(f"  • {error}")
        
        print()
        print("✅ Update complete!")
        print()
        print("⚠️  IMPORTANT:")
        print("  • Ensure setup_sales_partner_permissions.py has been run")
        print("  • Users are now Portal Users (Website User type)")
        print("  • They can only access commission data via portal")
        print("  • User Permissions ensure data isolation")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Fatal error in update_existing_sales_partners: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    update_sales_partner_users()

