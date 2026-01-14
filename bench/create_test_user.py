#!/usr/bin/env python3
"""Create test user for intake form testing"""
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
    user_email = 'testpatient@example.com'
    if not frappe.db.exists('User', user_email):
        user = frappe.get_doc({
            'doctype': 'User',
            'email': user_email,
            'first_name': 'Test',
            'last_name': 'Patient',
            'send_welcome_email': 0
        })
        user.insert(ignore_permissions=True)
        user.new_password = 'TestPatient123!'
        user.save(ignore_permissions=True)
        print(f'✓ Created user: {user_email} with password: TestPatient123!')
    else:
        # Update password
        user = frappe.get_doc('User', user_email)
        user.new_password = 'TestPatient123!'
        user.save(ignore_permissions=True)
        print(f'✓ User exists, password reset: {user_email} / TestPatient123!')
    
    frappe.db.commit()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

