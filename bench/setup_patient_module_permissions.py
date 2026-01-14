#!/usr/bin/env python3
"""Setup module permissions for Patient role - block Drive module"""
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

print('Setting up module permissions for Patient role...\n')

# Check if Drive module exists
drive_module = frappe.db.get_value('Module Def', {'module_name': 'Drive'}, 'name')
if drive_module:
    print(f'✓ Found Drive module')
else:
    print('⚠ Drive module not found in system')

# Create or update Module Profile for Patients
module_profile_name = 'Patient Module Profile'

if frappe.db.exists('Module Profile', module_profile_name):
    print(f'\nModule Profile "{module_profile_name}" already exists. Updating...')
    profile = frappe.get_doc('Module Profile', module_profile_name)
else:
    print(f'\nCreating Module Profile "{module_profile_name}"...')
    profile = frappe.get_doc({
        'doctype': 'Module Profile',
        'module_profile_name': module_profile_name
    })

# Clear existing blocked modules and add Drive
profile.block_modules = []
if drive_module:
    profile.append('block_modules', {'module': 'Drive'})
    print('✓ Added Drive to blocked modules')

# Save the profile
profile.save(ignore_permissions=True)
frappe.db.commit()
print(f'✓ Module Profile "{module_profile_name}" saved\n')

# Update all existing Patient users
patient_users = frappe.get_all('Has Role', 
    filters={'role': 'Patient'}, 
    fields=['parent'],
    distinct=True
)

print(f'Found {len(patient_users)} users with Patient role')

if patient_users:
    print('\nUpdating existing Patient users...')
    updated = 0
    for user_role in patient_users:
        user_name = user_role.parent
        try:
            user = frappe.get_doc('User', user_name)
            if user.module_profile != module_profile_name:
                user.module_profile = module_profile_name
                user.save(ignore_permissions=True)
                updated += 1
        except Exception as e:
            print(f'  ⚠ Error updating {user_name}: {e}')
    
    if updated > 0:
        frappe.db.commit()
        print(f'\n✓ Updated {updated} Patient users with module profile')
    else:
        print('\n✓ All Patient users already have the correct module profile')

print('\n✅ Module permissions setup complete!')
print(f'\nModule Profile: {module_profile_name}')
print(f'Blocked Modules: Drive')
print(f'\nNew Patient signups will automatically get this module profile.')
print(f'\nTo view/edit: http://localhost:8000/app/module-profile/{module_profile_name}')

frappe.destroy()

