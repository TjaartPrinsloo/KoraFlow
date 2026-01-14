#!/usr/bin/env python3
"""
Remove Default Workspace from Administrator

Administrator should not have a default workspace set.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print('Removing default workspace from Administrator...')
    
    admin = frappe.get_doc('User', 'Administrator')
    if admin.default_workspace:
        print(f'  Current default_workspace: {admin.default_workspace}')
        admin.default_workspace = None
        admin.flags.ignore_permissions = True
        admin.save()
        frappe.db.commit()
        print('  ✓ Removed default workspace')
    else:
        print('  ✓ Administrator already has no default workspace')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

