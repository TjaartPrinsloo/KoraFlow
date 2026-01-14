#!/usr/bin/env python3
"""
Add Sales Invoice Read Permission for Sales Partner Portal Role

The Number Card has_permission() function checks if the user has read access
to the document_type. Since our Number Cards use Sales Invoice as document_type,
the Sales Partner Portal role needs read permission on Sales Invoice.
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

role = 'Sales Partner Portal'

try:
    print(f'Checking Sales Invoice permissions for role: {role}')
    print()
    
    # Get Sales Invoice DocType
    si_dt = frappe.get_doc('DocType', 'Sales Invoice')
    
    # Check if permission exists
    existing = [p for p in si_dt.permissions if p.role == role]
    
    if existing:
        perm = existing[0]
        print(f'Existing permission: Read={perm.read}, Write={perm.write}')
        if not perm.read:
            print('  Updating to add read permission...')
            perm.read = 1
            si_dt.flags.ignore_permissions = True
            si_dt.save()
            frappe.db.commit()
            print('  ✓ Added read permission')
        else:
            print('  ✓ Read permission already exists')
    else:
        print('  No permission found, adding...')
        si_dt.append('permissions', {
            'role': role,
            'read': 1,
            'write': 0,
            'create': 0,
            'delete': 0,
            'submit': 0,
            'cancel': 0,
            'amend': 0,
            'report': 0,
            'export': 0,
            'print': 0,
            'email': 0,
            'share': 0,
        })
        si_dt.flags.ignore_permissions = True
        si_dt.save()
        frappe.db.commit()
        print('  ✓ Added read permission')
    
    print()
    print('Note: User Permissions will still restrict Sales Partners to only see')
    print('      invoices where sales_partner matches their own Sales Partner.')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

