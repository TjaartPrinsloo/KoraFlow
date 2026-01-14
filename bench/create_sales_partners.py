#!/usr/bin/env python3
"""
Create Sales Partners and User Accounts for 3rd Party Agents

This script creates:
1. Sales Partner records for each agent
2. User accounts for each sales partner
3. Links users to Sales User role

Run this script in production with:
    bench --site koraflow-site execute create_sales_partners.create_sales_partners
"""

import sys
import os
import re
import secrets
import string

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

# List of sales partner names
SALES_PARTNERS = [
    "Adri Kotze",
    "Anita Graham",
    "Anke Balt",
    "Anna Maria Hattingh",
    "Annamarie Louw",
    "Anzel van der Merwe",
    "Belinda Scharneck",
    "Carike van Vuuren",
    "Chané van Biljon",
    "Chantelle Meyer",
    "Charnice Venter",
    "Cherise Delport",
    "Christelle van Wyk",
    "Clarissa Human",
    "Elmee Ellerbeck",
    "Erika du Toit (Potch Diet Clinic)",
    "Jacky de Jager",
    "Janine Cronje",
    "Jean Breedt (Bodylab Potch)",
    "Jeanne-Mari Uys",
    "Jorine Rich",
    "Karin Ferreira",
    "Le-Lue van der Sandt",
    "Liani Rossouw",
    "Liezel Swart",
    "Lizette Enslin",
    "Lizette Labuschagne",
    "Madie Strydom",
    "Marisa Vorster",
    "Marizelle de Beer",
    "Marli de Villiers",
    "Michelle Potgieter",
    "Monica Swanepoel",
    "Monya Oosthuizen",
    "Petro Enslin",
    "Reta Britz",
    "Riëtte Viljoen",
    "Salomé Gouws",
    "Seanari Sharneck",
    "Sone Bosman",
    "Sonette Viljoen",
    "Teneil Bierman",
    "Terrence Abrahams",
    "Theresa Visser",
    "Zell Lombard",
    "Zelmé de Villiers",
]


def generate_email_from_name(full_name, existing_emails=None):
    """Generate email address from full name, handling duplicates"""
    if existing_emails is None:
        existing_emails = set()
    
    # Remove special characters and extra spaces
    name = re.sub(r'[()]', '', full_name)  # Remove parentheses
    name = re.sub(r'\s+', ' ', name).strip()  # Normalize spaces
    
    # Split into parts
    parts = name.split()
    
    base_email = None
    if len(parts) >= 2:
        # Use first name and last name
        first_name = parts[0].lower()
        last_name = parts[-1].lower()
        # Remove special characters from names
        first_name = re.sub(r'[^a-z0-9]', '', first_name)
        last_name = re.sub(r'[^a-z0-9]', '', last_name)
        base_email = f"{first_name}.{last_name}"
    else:
        # Fallback: use the whole name
        base_email = re.sub(r'[^a-z0-9]', '', name.lower())
    
    # Check for duplicates and add number if needed
    email = f"{base_email}@koraflow.com"
    counter = 1
    while email in existing_emails:
        email = f"{base_email}{counter}@koraflow.com"
        counter += 1
    
    # Also check database if frappe is connected
    if frappe.db:
        original_email = email
        counter = 1
        while frappe.db.exists("User", email):
            email = f"{base_email}{counter}@koraflow.com"
            counter += 1
            # Prevent infinite loop
            if counter > 100:
                break
    
    return email


def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def get_or_create_default_territory():
    """Get default territory or create one if it doesn't exist"""
    # Try common default territories
    default_territories = ["All Territories", "Rest Of The World"]
    
    for territory_name in default_territories:
        if frappe.db.exists("Territory", territory_name):
            return territory_name
    
    # If none exist, try to get any territory
    territories = frappe.get_all("Territory", limit=1)
    if territories:
        return territories[0].name
    
    # Create a default territory if none exists
    try:
        territory = frappe.get_doc({
            "doctype": "Territory",
            "territory_name": "All Territories",
            "is_group": 1
        })
        territory.insert(ignore_permissions=True)
        frappe.db.commit()
        return "All Territories"
    except Exception as e:
        frappe.log_error(f"Error creating default territory: {str(e)}")
        # Fallback: return a string that might work
        return "All Territories"


def create_sales_partner_and_user(full_name, territory, commission_rate=0.0, existing_emails=None):
    """Create a Sales Partner and associated User account"""
    if existing_emails is None:
        existing_emails = set()
    
    results = {
        "name": full_name,
        "sales_partner_created": False,
        "user_created": False,
        "user_permission_created": False,
        "email": None,
        "password": None,
        "errors": []
    }
    
    try:
        # Generate email from name (check for duplicates)
        email = generate_email_from_name(full_name, existing_emails=existing_emails)
        results["email"] = email
        
        # Check if sales partner already exists
        if frappe.db.exists("Sales Partner", full_name):
            results["errors"].append(f"Sales Partner '{full_name}' already exists")
            return results
        
        # Check if user already exists
        if frappe.db.exists("User", email):
            results["errors"].append(f"User '{email}' already exists")
            return results
        
        # Generate password
        password = generate_password()
        results["password"] = password
        
        # Create Sales Partner
        sales_partner = frappe.get_doc({
            "doctype": "Sales Partner",
            "partner_name": full_name,
            "territory": territory,
            "commission_rate": commission_rate,
        })
        sales_partner.flags.ignore_permissions = True
        sales_partner.insert()
        results["sales_partner_created"] = True
        
        # Parse name for user
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else full_name
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Create User account as Website User (Portal User, NOT Desk access)
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "user_type": "Website User",  # Portal user, NOT System User
            "send_welcome_email": 0,  # Don't send welcome email
        })
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()
        
        # Set password
        user.new_password = password
        user.save(ignore_permissions=True)
        
        # Add Sales Partner Portal role (will be created by setup script)
        # Check if role exists, if not use a fallback
        if frappe.db.exists("Role", "Sales Partner Portal"):
            user.add_roles("Sales Partner Portal")
        else:
            # Fallback: will be updated by setup script
            print(f"  ⚠️  Warning: Sales Partner Portal role not found. User created but role not assigned.")
            print(f"     Run setup_sales_partner_permissions.py to complete setup.")
        
        # Assign Module Profile to block Drive
        if frappe.db.exists("Module Profile", "Sales Partner Module Profile"):
            user.module_profile = "Sales Partner Module Profile"
            user.flags.ignore_permissions = True
            user.save(ignore_permissions=True)
        
        # Create User Permission for Sales Partner to isolate data
        # This ensures they only see records where sales_partner = their own
        try:
            # Remove existing permission if any
            existing_perm = frappe.db.get_value('User Permission', 
                {'user': email, 'allow': 'Sales Partner'}, 'name')
            if existing_perm:
                frappe.delete_doc('User Permission', existing_perm, ignore_permissions=True)
            
            # Create User Permission
            user_perm = frappe.get_doc({
                'doctype': 'User Permission',
                'user': email,
                'allow': 'Sales Partner',
                'for_value': full_name,  # The Sales Partner name
                'apply_to_all_doctypes': 1,  # Apply to all doctypes
            })
            user_perm.flags.ignore_permissions = True
            user_perm.insert()
            results["user_permission_created"] = True
        except Exception as perm_error:
            results["errors"].append(f"User Permission creation failed: {str(perm_error)}")
            frappe.log_error(f"User Permission error for {full_name}: {str(perm_error)}")
        
        results["user_created"] = True
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Error creating {full_name}: {str(e)}"
        results["errors"].append(error_msg)
        frappe.log_error(error_msg, f"Sales Partner Creation Error: {full_name}")
    
    return results


def create_sales_partners(site='koraflow-site'):
    """Main function to create all sales partners and users"""
    # If frappe is not initialized, initialize it
    if not frappe.db:
        frappe.init(site=site)
        frappe.connect()
    
    try:
        # Get or create default territory
        territory = get_or_create_default_territory()
        print(f"Using territory: {territory}\n")
        
        # Store results
        all_results = []
        successful = 0
        failed = 0
        skipped = 0
        created_emails = set()  # Track emails to avoid duplicates
        
        print("Creating Sales Partners and User Accounts...")
        print("=" * 80)
        
        for name in SALES_PARTNERS:
            result = create_sales_partner_and_user(name, territory, existing_emails=created_emails)
            if result["email"]:
                created_emails.add(result["email"])
            all_results.append(result)
            
            if result["errors"]:
                if "already exists" in str(result["errors"]):
                    skipped += 1
                    status = "SKIPPED"
                else:
                    failed += 1
                    status = "FAILED"
            else:
                successful += 1
                status = "SUCCESS"
            
            print(f"{status}: {name}")
            if result["email"]:
                print(f"  Email: {result['email']}")
            if result["password"]:
                print(f"  Password: {result['password']}")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"  Error: {error}")
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total: {len(SALES_PARTNERS)}")
        print(f"Successful: {successful}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        print()
        
        # Save credentials to file
        credentials_file = os.path.join(bench_dir, "sales_partner_credentials.txt")
        with open(credentials_file, "w") as f:
            f.write("Sales Partner Credentials\n")
            f.write("=" * 80 + "\n\n")
            for result in all_results:
                if result["user_created"]:
                    f.write(f"Name: {result['name']}\n")
                    f.write(f"Email: {result['email']}\n")
                    f.write(f"Password: {result['password']}\n")
                    f.write("-" * 80 + "\n")
        
        print(f"Credentials saved to: {credentials_file}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Fatal error in create_sales_partners: {str(e)}", "Sales Partner Creation Fatal Error")
    finally:
        frappe.destroy()


if __name__ == "__main__":
    # Allow site to be passed as command line argument
    site = sys.argv[1] if len(sys.argv) > 1 else 'koraflow-site'
    create_sales_partners(site=site)

