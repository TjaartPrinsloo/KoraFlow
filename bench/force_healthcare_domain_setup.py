#!/usr/bin/env python3
"""Force Healthcare domain setup to add custom fields"""
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

print('Forcing Healthcare domain setup...\n')
print('='*60)

# Get Domain Settings and trigger on_update
domain_settings = frappe.get_single("Domain Settings")

# Ensure Healthcare is in active domains
if "Healthcare" not in [d.domain for d in domain_settings.active_domains]:
    domain_settings.set_active_domains(["Healthcare"])
    print('✓ Added Healthcare to active domains')

# Trigger on_update which calls setup_domain
print('\nTriggering domain setup (this adds custom fields)...')
try:
    domain_settings.on_update()
    frappe.db.commit()
    print('✓ Domain setup triggered')
except Exception as e:
    print(f'⚠️  Error: {e}')
    import traceback
    traceback.print_exc()

# Also try calling setup_domain directly on Healthcare domain
if frappe.db.exists("Domain", "Healthcare"):
    print('\nCalling setup_domain directly on Healthcare domain...')
    try:
        domain = frappe.get_doc("Domain", "Healthcare")
        domain.setup_domain()
        frappe.db.commit()
        print('✓ Direct domain setup completed')
    except Exception as e:
        print(f'⚠️  Error: {e}')

# Clear all caches
frappe.clear_cache()
frappe.cache().delete_value('active_domains')
print('✓ Cache cleared')

# Verify
print('\nVerifying fields...')
item_meta = frappe.get_meta("Item")
healthcare_fields = [
    'generic_name', 'strength', 'strength_uom', 'dosage_form',
    'route_of_administration', 'volume', 'volume_uom',
    'legal_status', 'product_control'
]

found = [f for f in healthcare_fields if item_meta.has_field(f)]
if found:
    print(f'\n✅ Found {len(found)}/{len(healthcare_fields)} Healthcare fields!')
    for f in found:
        print(f'  ✓ {f}')
else:
    print(f'\n⚠️  Fields still not found')
    print('\nNext steps:')
    print('  1. Go to: http://localhost:8000/app/domain-settings')
    print('  2. Make sure Healthcare is checked')
    print('  3. Click Save')
    print('  4. Refresh the Item form')

frappe.destroy()

