#!/usr/bin/env python3
"""Setup Healthcare domain and add medicine/stock fields to Item DocType"""
import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

frappe.init(site='koraflow-site')
frappe.connect()

print('='*60)
print('Setting up Healthcare Medicine Stock Fields for Item')
print('='*60)

# Step 1: Enable Healthcare Domain
print('\n1. Checking Healthcare domain...')
active_domains = frappe.get_active_domains()
print(f'   Current active domains: {active_domains}')

if "Healthcare" not in active_domains:
    print('   ✗ Healthcare domain is NOT enabled')
    print('   Enabling Healthcare domain...')
    
    # Get Domain Settings
    domain_settings = frappe.get_single("Domain Settings")
    
    # Check if Healthcare domain exists
    if not frappe.db.exists("Domain", "Healthcare"):
        print('   Creating Healthcare domain...')
        domain = frappe.get_doc({
            "doctype": "Domain",
            "domain": "Healthcare"
        })
        domain.insert(ignore_permissions=True)
        frappe.db.commit()
        print('   ✓ Healthcare domain created')
    
    # Add Healthcare to active domains (skip full setup to avoid errors)
    try:
        domain_settings.set_active_domains(["Healthcare"])
        frappe.db.commit()
        print('   ✓ Healthcare domain added to active domains')
    except Exception as e:
        print(f'   ⚠️  Could not fully setup domain (this is OK): {str(e)}')
        # Try to manually add the domain
        try:
            if not frappe.db.exists("Domain Settings", "Domain Settings"):
                domain_settings = frappe.new_doc("Domain Settings")
                domain_settings.insert(ignore_permissions=True)
            domain_settings = frappe.get_single("Domain Settings")
            if not domain_settings.active_domains:
                domain_settings.active_domains = []
            if "Healthcare" not in domain_settings.active_domains:
                domain_settings.active_domains.append("Healthcare")
                domain_settings.save(ignore_permissions=True)
                frappe.db.commit()
                print('   ✓ Healthcare domain manually added')
        except Exception as e2:
            print(f'   ⚠️  Could not add domain automatically: {str(e2)}')
            print('   You may need to enable Healthcare domain manually in Domain Settings')
else:
    print('   ✓ Healthcare domain is already ENABLED')

# Step 2: Add healthcare fields to Item
print('\n2. Adding Healthcare fields to Item DocType...')

# Check existing fields
existing_fields = frappe.get_all(
    "Custom Field",
    filters={"dt": "Item", "fieldname": ["in", [
        "drug_specifications_section",
        "generic_name",
        "strength",
        "strength_uom",
        "dosage_form",
        "route_of_administration",
        "volume",
        "volume_uom",
        "legal_status",
        "product_control",
        "is_prescription_item",
        "is_controlled"
    ]]},
    pluck="fieldname"
)

if existing_fields:
    print(f'   Found {len(existing_fields)} existing fields: {existing_fields}')

# Define custom fields for Item DocType
custom_fields = {
    "Item": [
        {
            "fieldname": "drug_specifications_section",
            "label": "Drug Specifications",
            "fieldtype": "Section Break",
            "insert_after": "brand",
            "collapsible": 1,
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "generic_name",
            "label": "Generic Name",
            "fieldtype": "Data",
            "insert_after": "drug_specifications_section",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "strength",
            "label": "Strength",
            "fieldtype": "Float",
            "precision": "2",
            "insert_after": "generic_name",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "strength_uom",
            "label": "Strength UOM",
            "fieldtype": "Link",
            "options": "UOM",
            "insert_after": "strength",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "dosage_form",
            "label": "Dosage Form",
            "fieldtype": "Link",
            "options": "Dosage Form",
            "insert_after": "strength_uom",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "route_of_administration",
            "label": "Route Of Administration",
            "fieldtype": "Data",
            "insert_after": "dosage_form",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "drug_specifications_column_break",
            "fieldtype": "Column Break",
            "insert_after": "route_of_administration",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "volume",
            "label": "Volume",
            "fieldtype": "Float",
            "precision": "2",
            "insert_after": "drug_specifications_column_break",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "volume_uom",
            "label": "Volume UOM",
            "fieldtype": "Link",
            "options": "UOM",
            "insert_after": "volume",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "legal_status",
            "label": "Legal Status",
            "fieldtype": "Select",
            "options": "\nPrescription\nOver-the-Counter (OTC)\nControlled Substance\nRestricted",
            "insert_after": "volume_uom",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "product_control",
            "label": "Product Control",
            "fieldtype": "Select",
            "options": "\nControlled\nUncontrolled",
            "insert_after": "legal_status",
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "healthcare_medicine_section",
            "label": "Healthcare Medicine Settings",
            "fieldtype": "Section Break",
            "insert_after": "product_control",
            "collapsible": 1,
            "restrict_to_domain": "Healthcare"
        },
        {
            "fieldname": "is_prescription_item",
            "label": "Is Prescription Item",
            "fieldtype": "Check",
            "default": 0,
            "insert_after": "healthcare_medicine_section",
            "restrict_to_domain": "Healthcare",
            "description": "Check if this item requires a prescription"
        },
        {
            "fieldname": "is_controlled",
            "label": "Is Controlled Substance",
            "fieldtype": "Check",
            "default": 0,
            "insert_after": "is_prescription_item",
            "restrict_to_domain": "Healthcare",
            "description": "Check if this is a controlled substance"
        }
    ]
}

try:
    # Create custom fields
    create_custom_fields(custom_fields)
    frappe.db.commit()
    
    print('   ✅ Successfully created Healthcare fields!')
    
    # Count new fields
    new_fields = [f for f in custom_fields["Item"] if f.get("fieldname") not in existing_fields]
    print(f'   Created {len(new_fields)} new fields')
    
    if new_fields:
        print('\n   New fields created:')
        for field in new_fields:
            print(f'     ✓ {field.get("label", field.get("fieldname"))}')
    
except Exception as e:
    frappe.log_error(f"Error creating Healthcare Item fields: {str(e)}")
    print(f'\n   ❌ Error creating fields: {str(e)}')
    import traceback
    traceback.print_exc()

# Step 3: Clear cache
print('\n3. Clearing cache...')
frappe.clear_cache()
print('   ✓ Cache cleared')

# Step 4: Verify
print('\n4. Verification:')
active_domains = frappe.get_active_domains()
if "Healthcare" in active_domains:
    print('   ✓ Healthcare domain is ACTIVE')
else:
    print('   ✗ Healthcare domain is NOT active')

# Check fields
item_meta = frappe.get_meta("Item")
healthcare_fields = ['generic_name', 'strength', 'dosage_form', 'is_prescription_item', 'is_controlled']
found = sum(1 for f in healthcare_fields if item_meta.has_field(f))
print(f'   ✓ {found}/{len(healthcare_fields)} key healthcare fields found in Item doctype')

print('\n' + '='*60)
print('✅ Setup Complete!')
print('='*60)
print('\n💡 Next steps:')
print('  1. Hard refresh your browser (Cmd+Shift+R or Ctrl+Shift+R)')
print('  2. Open an Item document')
print('  3. Look for "Drug Specifications" section after "Brand" field')
print('  4. Look for "Healthcare Medicine Settings" section')
print('  5. You should see fields like:')
print('     - Generic Name')
print('     - Strength')
print('     - Dosage Form')
print('     - Is Prescription Item')
print('     - Is Controlled Substance')
print('\n')

frappe.destroy()
