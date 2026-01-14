#!/usr/bin/env python3
"""Fix 404 errors for JavaScript files"""
import sys
import os
import shutil

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

print('Fixing JavaScript file 404 errors...\n')
print('='*60)

# Files that need to be accessible
files_to_fix = [
    {
        'source': 'apps/koraflow_core/koraflow_core/public/js/signup_redirect.js',
        'web_path': 'koraflow_core/js/signup_redirect.js',
        'assets_path': 'sites/assets/koraflow_core/js/signup_redirect.js'
    },
    {
        'source': 'apps/koraflow_core/koraflow_core/public/web_form/glp1_intake/glp1_intake.js',
        'web_path': 'koraflow_core/web_form/glp1_intake/glp1_intake.js',
        'assets_path': 'sites/assets/koraflow_core/web_form/glp1_intake/glp1_intake.js'
    }
]

for file_info in files_to_fix:
    source = file_info['source']
    assets_path = file_info['assets_path']
    web_path = file_info['web_path']
    
    print(f'\nProcessing: {web_path}')
    
    # Check if source exists
    if not os.path.exists(source):
        print(f'  ✗ Source file not found: {source}')
        continue
    
    # Ensure assets directory exists
    assets_dir = os.path.dirname(assets_path)
    os.makedirs(assets_dir, exist_ok=True)
    print(f'  ✓ Assets directory: {assets_dir}')
    
    # Copy to assets
    try:
        shutil.copy2(source, assets_path)
        print(f'  ✓ Copied to: {assets_path}')
    except Exception as e:
        print(f'  ✗ Error copying: {e}')

# Also check if files are in the right public location
print('\n' + '='*60)
print('Verifying public directory structure...\n')

public_base = 'apps/koraflow_core/koraflow_core/public'
expected_files = [
    'js/signup_redirect.js',
    'web_form/glp1_intake/glp1_intake.js'
]

for rel_path in expected_files:
    full_path = os.path.join(public_base, rel_path)
    if os.path.exists(full_path):
        print(f'✓ {rel_path} exists')
    else:
        print(f'✗ {rel_path} NOT FOUND')

# Clear caches
print('\n' + '='*60)
print('Clearing caches...')
frappe.clear_cache()
print('✓ Cache cleared')

frappe.destroy()

print('\n' + '='*60)
print('✅ Fix complete!')
print('\nFiles should now be accessible.')
print('If you still see 404s, try:')
print('  1. Hard refresh browser (Cmd+Shift+R)')
print('  2. Clear browser cache')
print('  3. Check browser console for exact URLs being requested')

