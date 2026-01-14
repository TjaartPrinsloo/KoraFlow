#!/usr/bin/env python3
"""Add Healthcare Drug Specifications custom fields to Item DocType"""
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

print('Adding Healthcare Drug Specifications fields to Item DocType...\n')
print('='*60)

# Check if fields already exist
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
        "product_control"
    ]]},
    pluck="fieldname"
)

if existing_fields:
    print(f'⚠️  Found {len(existing_fields)} existing fields: {existing_fields}')
    print('Skipping creation of existing fields...\n')

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
        }
    ]
}

try:
    # Create custom fields
    create_custom_fields(custom_fields)
    frappe.db.commit()
    
    print('✅ Successfully created Healthcare Drug Specifications fields!')
    print('\nCreated fields:')
    for doctype, fields in custom_fields.items():
        for field in fields:
            if field.get("fieldname") not in existing_fields:
                field_type = field.get("fieldtype", "")
                label = field.get("label", field.get("fieldname", ""))
                print(f'  ✓ {label} ({field_type})')
    
    print('\n💡 Next steps:')
    print('  1. Clear cache: bench clear-cache')
    print('  2. Refresh your browser (Cmd+Shift+R)')
    print('  3. Open an Item document - you should see "Drug Specifications" section')
    print('  4. Fields will only appear when Healthcare domain is active')
    
except Exception as e:
    frappe.log_error(f"Error creating Healthcare Item fields: {str(e)}")
    print(f'\n❌ Error creating fields: {str(e)}')
    import traceback
    traceback.print_exc()

frappe.destroy()

