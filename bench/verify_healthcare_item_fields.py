#!/usr/bin/env python3
"""Verify Healthcare Drug Specifications fields were created"""
import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

# Clear all caches
frappe.clear_cache()
frappe.cache().delete_value('active_domains')
frappe.cache().delete_value('active_modules')
print('✓ Cache cleared')

# Verify fields were created
print('\nVerifying created fields...\n')
print('='*60)

custom_fields = frappe.get_all(
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
    fields=["fieldname", "label", "fieldtype"]
)

print(f'Found {len(custom_fields)} custom fields:\n')
for cf in custom_fields:
    print(f'  ✓ {cf.label} ({cf.fieldtype})')

# Check Item meta to see if fields are accessible
item_meta = frappe.get_meta("Item")
healthcare_fields = ['generic_name', 'strength', 'strength_uom', 'dosage_form', 
                     'route_of_administration', 'volume', 'volume_uom', 
                     'legal_status', 'product_control']

found = [f for f in healthcare_fields if item_meta.has_field(f)]
print(f'\n✅ {len(found)}/{len(healthcare_fields)} fields are accessible in Item DocType')

if len(found) == len(healthcare_fields):
    print('\n🎉 All Healthcare Drug Specifications fields are ready!')
    print('\nTo see them:')
    print('  1. Open an Item document in the UI')
    print('  2. Look for the "Drug Specifications" section (after "Brand" field)')
    print('  3. Fields will only appear when Healthcare domain is active')
else:
    missing = [f for f in healthcare_fields if f not in found]
    print(f'\n⚠️  Missing fields: {missing}')

frappe.destroy()

