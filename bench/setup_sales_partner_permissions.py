#!/usr/bin/env python3
"""
Setup Sales Partner Portal Role and Permissions

This script:
1. Creates "Sales Partner Portal" role
2. Removes access to sensitive doctypes (Patient, Invoice, Prescriptions, Stock, Desk)
3. Grants read-only access to commission-related doctypes only
4. Updates existing sales partner users to use the new role

Run with:
    python3 setup_sales_partner_permissions.py
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

# Sensitive doctypes that Sales Partners should NOT access
BLOCKED_DOCTYPES = [
    # Healthcare
    "Patient",
    "Patient Encounter",
    "Medication",
    "Prescription",
    "Lab Test",
    "Lab Test Template",
    "Vital Signs",
    "Clinical Procedure",
    
    # Financial
    "Sales Invoice",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
    "Account",
    "Cost Center",
    "Payment Request",
    
    # Inventory/Stock
    "Item",
    "Stock Entry",
    "Stock Reconciliation",
    "Material Request",
    "Purchase Receipt",
    "Delivery Note",
    "Warehouse",
    "Bin",
    "Stock Ledger Entry",
    
    # Sales/Purchase
    "Sales Order",
    "Purchase Order",
    "Quotation",
    "Sales Return",
    "Purchase Return",
    
    # System
    "Company",
    "Fiscal Year",
    "Currency",
    "Country",
    "Territory",
    "Customer",
    "Supplier",
    "Employee",
    "User",
    "Role",
    "Permission Manager",
    "Customize Form",
    "Workspace",
    
    # Other sensitive
    "Communication",
    "File",
    "Note",
    "ToDo",
    "Event",
]

# Commission-related doctypes (read-only access)
COMMISSION_DOCTYPES = [
    "Sales Partner",  # Their own Sales Partner record
]

# Commission-related Reports (read-only access)
COMMISSION_REPORTS = [
    "Sales Partner Commission Summary",
    "Sales Partners Commission",
    "Sales Partner Transaction Summary",
]

ROLE_NAME = "Sales Partner Portal"


def create_sales_partner_portal_role():
    """Create the Sales Partner Portal role if it doesn't exist"""
    if frappe.db.exists("Role", ROLE_NAME):
        print(f"✓ Role '{ROLE_NAME}' already exists")
        return True
    
    try:
        role = frappe.get_doc({
            "doctype": "Role",
            "role_name": ROLE_NAME,
            "desk_access": 0,  # NO Desk access - portal only
        })
        role.flags.ignore_permissions = True
        role.insert()
        frappe.db.commit()
        print(f"✓ Created role: {ROLE_NAME}")
        return True
    except Exception as e:
        print(f"❌ Error creating role: {e}")
        frappe.log_error(f"Error creating role {ROLE_NAME}: {str(e)}")
        return False


def remove_permissions_for_doctype(role_name, doctype):
    """Remove all permissions for a doctype for a role"""
    # Get all permission records for this role and doctype
    permissions = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": doctype, "role": role_name},
        fields=["name"]
    )
    
    for perm in permissions:
        try:
            frappe.delete_doc("Custom DocPerm", perm.name, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error deleting permission for {doctype}: {str(e)}")
    
    # Also check standard permissions
    standard_perms = frappe.get_all(
        "DocPerm",
        filters={"parent": doctype, "role": role_name},
        fields=["name"]
    )
    
    for perm in standard_perms:
        try:
            frappe.delete_doc("DocPerm", perm.name, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error deleting standard permission for {doctype}: {str(e)}")


def block_doctype_access(role_name, doctype):
    """Block access to a doctype by removing all permissions"""
    if not frappe.db.exists("DocType", doctype):
        return
    
    # Remove existing permissions
    remove_permissions_for_doctype(role_name, doctype)
    
    # Create explicit deny permissions (if needed)
    # Actually, removing permissions is enough - no permission = no access
    print(f"  ✓ Blocked: {doctype}")


def grant_readonly_access(role_name, doctype):
    """Grant read-only access to a doctype"""
    if not frappe.db.exists("DocType", doctype):
        print(f"  ⚠️  DocType not found: {doctype}")
        return
    
    # Remove existing permissions first
    remove_permissions_for_doctype(role_name, doctype)
    
    # Get the doctype document
    try:
        doctype_doc = frappe.get_doc("DocType", doctype)
        
        # Check if custom permission already exists
        existing = frappe.db.get_value(
            "Custom DocPerm",
            {"parent": doctype, "role": role_name, "permlevel": 0},
            "name"
        )
        
        if existing:
            perm_doc = frappe.get_doc("Custom DocPerm", existing)
        else:
            perm_doc = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role_name,
                "permlevel": 0,
            })
        
        # Set read-only permissions
        perm_doc.read = 1
        perm_doc.write = 0
        perm_doc.create = 0
        perm_doc.delete = 0
        perm_doc.submit = 0
        perm_doc.cancel = 0
        perm_doc.amend = 0
        perm_doc.report = 0
        perm_doc.export = 0
        perm_doc.print = 0
        perm_doc.email = 0
        perm_doc.share = 0
        
        perm_doc.flags.ignore_permissions = True
        if existing:
            perm_doc.save()
        else:
            doctype_doc.append("permissions", perm_doc)
            doctype_doc.flags.ignore_permissions = True
            doctype_doc.save()
        
        print(f"  ✓ Read-only access: {doctype}")
    except Exception as e:
        print(f"  ❌ Error setting permissions for {doctype}: {e}")
        frappe.log_error(f"Error setting permissions for {doctype}: {str(e)}")


def grant_report_access(role_name, report_name):
    """Grant access to a report"""
    if not frappe.db.exists("Report", report_name):
        print(f"  ⚠️  Report not found: {report_name}")
        return
    
    try:
        report_doc = frappe.get_doc("Report", report_name)
        
        # Check if role already has access
        roles = [r.role for r in report_doc.roles]
        
        if role_name not in roles:
            report_doc.append("roles", {"role": role_name})
            report_doc.flags.ignore_permissions = True
            report_doc.save()
            print(f"  ✓ Report access: {report_name}")
        else:
            print(f"  ✓ Report already accessible: {report_name}")
    except Exception as e:
        print(f"  ❌ Error granting report access for {report_name}: {e}")
        frappe.log_error(f"Error granting report access for {report_name}: {str(e)}")


def create_sales_partner_module_profile():
    """Create Module Profile to block Drive for Sales Partners"""
    profile_name = "Sales Partner Module Profile"
    
    if frappe.db.exists("Module Profile", profile_name):
        print(f"✓ Module Profile '{profile_name}' already exists")
        return profile_name
    
    try:
        # Check if Drive module exists
        if not frappe.db.exists("Module Def", {"module_name": "Drive"}):
            print("⚠️  Drive module not found, skipping Module Profile creation")
            return None
        
        profile = frappe.get_doc({
            "doctype": "Module Profile",
            "module_profile_name": profile_name,
        })
        
        # Block Drive module
        profile.append("block_modules", {"module": "Drive"})
        
        profile.flags.ignore_permissions = True
        profile.insert()
        frappe.db.commit()
        print(f"✓ Created Module Profile: {profile_name} (blocks Drive)")
        return profile_name
    except Exception as e:
        print(f"❌ Error creating Module Profile: {e}")
        frappe.log_error(f"Error creating Module Profile {profile_name}: {str(e)}")
        return None


def assign_module_profile_to_users():
    """Assign Sales Partner Module Profile to all sales partner users"""
    profile_name = "Sales Partner Module Profile"
    
    if not frappe.db.exists("Module Profile", profile_name):
        print(f"⚠️  Module Profile '{profile_name}' not found. Run create_sales_partner_module_profile first.")
        return 0
    
    # Find all users with Sales Partner Portal role
    users = frappe.get_all(
        "Has Role",
        filters={"role": "Sales Partner Portal"},
        fields=["parent"]
    )
    
    updated = 0
    for user_role in users:
        user_email = user_role.parent
        try:
            user_doc = frappe.get_doc("User", user_email)
            if user_doc.module_profile != profile_name:
                user_doc.module_profile = profile_name
                user_doc.flags.ignore_permissions = True
                user_doc.save()
                updated += 1
                print(f"  ✓ Assigned Module Profile to: {user_email}")
        except Exception as e:
            print(f"  ❌ Error updating {user_email}: {e}")
            frappe.log_error(f"Error assigning Module Profile to {user_email}: {str(e)}")
    
    return updated


def update_existing_users():
    """Update existing sales partner users to use the new role"""
    # Find all users with Sales Partner Portal role or who are linked to Sales Partners
    users = frappe.get_all(
        "User",
        filters={"user_type": "Website User"},
        fields=["name", "email"]
    )
    
    updated = 0
    for user in users:
        # Check if user has a Sales Partner User Permission
        has_sp_permission = frappe.db.exists(
            "User Permission",
            {"user": user.name, "allow": "Sales Partner"}
        )
        
        if has_sp_permission:
            # Add Sales Partner Portal role if not already assigned
            user_doc = frappe.get_doc("User", user.name)
            roles = [r.role for r in user_doc.roles]
            
            if ROLE_NAME not in roles:
                user_doc.add_roles(ROLE_NAME)
                # Remove Sales User role if present
                if "Sales User" in roles:
                    user_doc.remove_roles("Sales User")
                user_doc.save(ignore_permissions=True)
                updated += 1
                print(f"  ✓ Updated user: {user.email}")
    
    return updated


def setup_permissions():
    """Main function to set up all permissions"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("SETTING UP SALES PARTNER PORTAL PERMISSIONS")
        print("=" * 80)
        print()
        
        # 1. Create role
        print("1️⃣ Creating Sales Partner Portal role...")
        if not create_sales_partner_portal_role():
            print("❌ Failed to create role. Exiting.")
            return
        print()
        
        # 2. Block access to sensitive doctypes
        print("2️⃣ Blocking access to sensitive doctypes...")
        for doctype in BLOCKED_DOCTYPES:
            block_doctype_access(ROLE_NAME, doctype)
        print()
        
        # 3. Grant read-only access to commission doctypes
        print("3️⃣ Granting read-only access to commission doctypes...")
        for doctype in COMMISSION_DOCTYPES:
            grant_readonly_access(ROLE_NAME, doctype)
        print()
        
        # 3b. Grant access to commission reports
        print("3b. Granting access to commission reports...")
        for report_name in COMMISSION_REPORTS:
            grant_report_access(ROLE_NAME, report_name)
        print()
        
        # 4. Create Module Profile to block Drive
        print("4️⃣ Creating Module Profile to block Drive...")
        module_profile = create_sales_partner_module_profile()
        print()
        
        # 5. Assign Module Profile to users
        if module_profile:
            print("5️⃣ Assigning Module Profile to sales partner users...")
            profile_updated = assign_module_profile_to_users()
            print(f"   Updated {profile_updated} users with Module Profile")
            print()
        
        # 6. Update existing users (role changes)
        print("6️⃣ Updating existing sales partner users...")
        updated = update_existing_users()
        print(f"   Updated {updated} users")
        print()
        
        frappe.db.commit()
        
        print("=" * 80)
        print("✅ SETUP COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  • Role: {ROLE_NAME}")
        print(f"  • Module Profile: Sales Partner Module Profile (blocks Drive)")
        print(f"  • Blocked doctypes: {len(BLOCKED_DOCTYPES)}")
        print(f"  • Commission doctypes (read-only): {len(COMMISSION_DOCTYPES)}")
        print(f"  • Commission reports: {len(COMMISSION_REPORTS)}")
        print(f"  • Updated users: {updated}")
        print()
        print("⚠️  IMPORTANT:")
        print("  • Sales Partners are Portal Users (Website User type)")
        print("  • They can ONLY see their own commission data via User Permissions")
        print("  • They have NO access to Desk, Patients, Invoices, Stock, etc.")
        print("  • All access is read-only for commission data")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Fatal error in setup_sales_partner_permissions: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    setup_permissions()

