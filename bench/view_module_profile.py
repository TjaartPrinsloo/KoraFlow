#!/usr/bin/env python3
"""View and edit Module Profile blocked modules"""
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

print('='*60)
print('PATIENT MODULE PROFILE - BLOCKED MODULES')
print('='*60)

profile = frappe.get_doc('Module Profile', 'Patient Module Profile')

print(f'\nProfile: {profile.name}')
print(f'\n✅ Currently Blocked Modules:')
if profile.block_modules:
    for block in profile.block_modules:
        print(f'  • {block.module} (will be hidden from Patient users)')
else:
    print('  (No modules currently blocked)')

print(f'\n📋 Users with this Profile:')
users = frappe.get_all('User', 
    filters={'module_profile': profile.name},
    fields=['name', 'email', 'enabled']
)
for user in users:
    status = 'Enabled' if user.enabled else 'Disabled'
    print(f'  • {user.email} ({status})')

print('\n' + '='*60)
print('NOTE: The "Connections" section in the UI shows related modules,')
print('      NOT the blocked modules. Blocked modules are configured')
print('      in a hidden field and managed via script.')
print('='*60)

frappe.destroy()

