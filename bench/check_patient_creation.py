#!/usr/bin/env python3
"""Check if patient and intake form were created"""
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
    
    # Check for Patient
    patient = frappe.db.get_value('Patient', {'email': user_email}, ['name', 'first_name', 'last_name', 'email'], as_dict=True)
    print(f'Patient: {patient if patient else "NOT FOUND"}')
    
    if patient:
        # Check for intake forms
        intake_forms = frappe.get_all('GLP-1 Intake Form', filters={'parent': patient.name}, fields=['name', 'form_status', 'first_name', 'last_name'], limit=5)
        print(f'Intake Forms: {intake_forms if intake_forms else "None"}')
        
        # Check for intake submissions
        submissions = frappe.get_all('GLP-1 Intake Submission', filters={'email': user_email}, fields=['name', 'first_name', 'last_name'], limit=5)
        print(f'Intake Submissions: {submissions if submissions else "None"}')
    else:
        print('No patient found - form may not have been submitted yet')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

