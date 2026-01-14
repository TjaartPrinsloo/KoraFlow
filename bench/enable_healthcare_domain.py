#!/usr/bin/env python3
"""Enable Healthcare domain to show additional Item fields"""
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

print('Enabling Healthcare domain...\n')
print('='*60)

# Check current active domains
active_domains = frappe.get_active_domains()
print(f'Current active domains: {active_domains}')

if "Healthcare" in active_domains:
    print('\n✓ Healthcare domain is already ENABLED')
    print('\nYou should see additional fields for Items/Stock:')
    print('  - Generic Name')
    print('  - Strength')
    print('  - Strength UOM')
    print('  - Dosage Form')
    print('  - Route Of Administration')
    print('  - Volume')
    print('  - Volume UOM')
    print('  - Legal Status')
    print('  - Product Control')
else:
    print('\n✗ Healthcare domain is NOT enabled')
    print('\nEnabling Healthcare domain...')
    
    # Get Domain Settings
    domain_settings = frappe.get_single("Domain Settings")
    
    # Check if Healthcare domain exists
    if not frappe.db.exists("Domain", "Healthcare"):
        print('Creating Healthcare domain...')
        domain = frappe.get_doc({
            "doctype": "Domain",
            "domain": "Healthcare"
        })
        domain.insert(ignore_permissions=True)
        frappe.db.commit()
        print('✓ Healthcare domain created')
    
    # Add Healthcare to active domains
    domain_settings.set_active_domains(["Healthcare"])
    frappe.db.commit()
    print('✓ Healthcare domain added to active domains')
    
    # Setup the domain (this adds custom fields, etc.)
    domain = frappe.get_doc("Domain", "Healthcare")
    domain.setup_domain()
    frappe.db.commit()
    print('✓ Healthcare domain setup completed')
    
    # Clear cache
    frappe.clear_cache()
    print('✓ Cache cleared')
    
    # Verify
    active_domains = frappe.get_active_domains()
    if "Healthcare" in active_domains:
        print('\n✅ Healthcare domain is now ACTIVE')
        print('\nYou should now see additional fields for Items/Stock:')
        print('  - Generic Name')
        print('  - Strength')
        print('  - Strength UOM')
        print('  - Dosage Form')
        print('  - Route Of Administration')
        print('  - Volume')
        print('  - Volume UOM')
        print('  - Legal Status')
        print('  - Product Control')
        print('\n💡 Tip: Refresh your browser or reload the Item form to see the new fields')
    else:
        print('\n⚠️  Healthcare domain is still not active')
        print('Please check Domain Settings manually')

frappe.destroy()

