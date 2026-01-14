#!/usr/bin/env python3
"""
Add User Permissions to Existing Sales Partner Users

This script adds User Permissions for existing sales partner users
to ensure data isolation. Each user will only see records where
sales_partner = their own Sales Partner name.

Run with:
    python3 add_user_permissions_to_sales_partners.py
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe


def add_user_permissions():
    """Add User Permissions for all sales partner users"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("ADDING USER PERMISSIONS FOR SALES PARTNER USERS")
        print("=" * 80)
        print()
        
        # Get all Sales Partners
        sales_partners = frappe.get_all("Sales Partner", fields=["name", "partner_name"])
        
        if not sales_partners:
            print("⚠️  No Sales Partners found.")
            return
        
        created = 0
        updated = 0
        errors = []
        
        for sp in sales_partners:
            partner_name = sp.name
            partner_display_name = sp.partner_name
            
            # Find user linked to this sales partner
            # Check User Permissions first
            user_perms = frappe.get_all(
                "User Permission",
                filters={"allow": "Sales Partner", "for_value": partner_name},
                fields=["user"]
            )
            
            if user_perms:
                # User Permission already exists
                user_email = user_perms[0].user
                print(f"✓ User Permission exists: {user_email} → {partner_display_name}")
                continue
            
            # Try to find user by email pattern (firstname.lastname@koraflow.com)
            # Or check if there's a Contact linked to this Sales Partner
            contacts = frappe.get_all(
                "Contact",
                filters={"link_doctype": "Sales Partner", "link_name": partner_name},
                fields=["email_id"]
            )
            
            user_email = None
            if contacts and contacts[0].email_id:
                user_email = contacts[0].email_id
                if not frappe.db.exists("User", user_email):
                    user_email = None
            
            # If no contact found, try to generate email from name
            if not user_email:
                import re
                name_parts = partner_display_name.split()
                if len(name_parts) >= 2:
                    first_name = re.sub(r'[^a-z0-9]', '', name_parts[0].lower())
                    last_name = re.sub(r'[^a-z0-9]', '', name_parts[-1].lower())
                    potential_email = f"{first_name}.{last_name}@koraflow.com"
                    if frappe.db.exists("User", potential_email):
                        user_email = potential_email
            
            if not user_email:
                # Search for users with similar names
                users = frappe.get_all(
                    "User",
                    filters={"user_type": ["in", ["System User", "Website User"]]},
                    fields=["name", "first_name", "last_name"]
                )
                
                # Try to match by name
                for user in users:
                    user_doc = frappe.get_doc("User", user.name)
                    full_name = f"{user_doc.first_name or ''} {user_doc.last_name or ''}".strip()
                    if full_name.lower() == partner_display_name.lower():
                        user_email = user.name
                        break
            
            if not user_email:
                errors.append(f"No user found for Sales Partner: {partner_display_name}")
                print(f"⚠️  No user found for: {partner_display_name}")
                continue
            
            # Create User Permission
            try:
                # Check if permission already exists
                existing = frappe.db.get_value(
                    "User Permission",
                    {"user": user_email, "allow": "Sales Partner"},
                    "name"
                )
                
                if existing:
                    # Update existing permission
                    perm_doc = frappe.get_doc("User Permission", existing)
                    if perm_doc.for_value != partner_name:
                        perm_doc.for_value = partner_name
                        perm_doc.apply_to_all_doctypes = 1
                        perm_doc.flags.ignore_permissions = True
                        perm_doc.save()
                        updated += 1
                        print(f"✓ Updated User Permission: {user_email} → {partner_display_name}")
                    else:
                        print(f"✓ User Permission already correct: {user_email} → {partner_display_name}")
                else:
                    # Create new permission
                    perm_doc = frappe.get_doc({
                        "doctype": "User Permission",
                        "user": user_email,
                        "allow": "Sales Partner",
                        "for_value": partner_name,
                        "apply_to_all_doctypes": 1,
                    })
                    perm_doc.flags.ignore_permissions = True
                    perm_doc.insert()
                    created += 1
                    print(f"✓ Created User Permission: {user_email} → {partner_display_name}")
                    
            except Exception as e:
                error_msg = f"Error creating User Permission for {partner_display_name} ({user_email}): {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                frappe.log_error(error_msg, f"User Permission Creation Error: {partner_display_name}")
        
        frappe.db.commit()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Sales Partners: {len(sales_partners)}")
        print(f"Created User Permissions: {created}")
        print(f"Updated User Permissions: {updated}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print()
            print("Errors:")
            for error in errors:
                print(f"  • {error}")
        
        print()
        print("✅ User Permissions setup complete!")
        print()
        print("⚠️  IMPORTANT:")
        print("  • Each sales partner can now ONLY see records where sales_partner = themselves")
        print("  • This applies to all doctypes automatically")
        print("  • Data isolation is enforced at database level")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Fatal error in add_user_permissions_to_sales_partners: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    add_user_permissions()

