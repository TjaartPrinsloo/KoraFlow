#!/usr/bin/env python3
"""Check if Healthcare fields are present on Item DocType"""
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

print('Checking Item DocType for Healthcare fields...\n')
print('='*60)

# Get Item DocType
item_meta = frappe.get_meta("Item")

# Healthcare-related fields
healthcare_fields = [
    'generic_name',
    'strength',
    'strength_uom',
    'dosage_form',
    'route_of_administration',
    'volume',
    'volume_uom',
    'legal_status',
    'product_control'
]

print('Checking for Healthcare fields in Item DocType:\n')
found_fields = []
missing_fields = []

for field_name in healthcare_fields:
    if item_meta.has_field(field_name):
        field = item_meta.get_field(field_name)
        found_fields.append(field_name)
        print(f'  ✓ {field_name} ({field.label})')
    else:
        missing_fields.append(field_name)
        print(f'  ✗ {field_name} - NOT FOUND')

if missing_fields:
    print(f'\n⚠️  {len(missing_fields)} fields are missing')
    print('These fields should be added by the Healthcare domain setup.')
    print('Try refreshing the Item form or check if Healthcare domain setup completed.')
else:
    print(f'\n✅ All {len(found_fields)} Healthcare fields are present!')
    print('\nTo see these fields:')
    print('  1. Open an Item document')
    print('  2. Look for the "Drug Specifications" section')
    print('  3. If not visible, click "Customize Form" and ensure fields are visible')
    print('  4. Hard refresh your browser (Cmd+Shift+R)')

# Check active domains
active_domains = frappe.get_active_domains()
print(f'\nActive domains: {active_domains}')

frappe.destroy()

