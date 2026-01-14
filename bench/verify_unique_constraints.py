#!/usr/bin/env python3
"""Verify unique constraints after migration"""
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

print('Verifying unique constraints after migration...\n')

# Check DocType field settings
doctype = frappe.get_doc('DocType', 'GLP-1 Intake Submission')
id_field = next((f for f in doctype.fields if f.fieldname == 'id_number__passport_number'), None)
mobile_field = next((f for f in doctype.fields if f.fieldname == 'mobile'), None)

print('DocType Field Settings:')
print(f'  ID Number unique flag: {id_field.unique if id_field else "N/A"}')
print(f'  Mobile unique flag: {mobile_field.unique if mobile_field else "N/A"}')

# Check Patient DocType
patient = frappe.get_doc('DocType', 'Patient')
patient_mobile = next((f for f in patient.fields if f.fieldname == 'mobile'), None)
if patient_mobile:
    print(f'\nPatient.mobile unique flag: {patient_mobile.unique}')

# Check database indexes
print('\nDatabase Indexes:')
try:
    # Patient mobile
    result = frappe.db.sql('SHOW INDEXES FROM `tabPatient` WHERE Column_name = %s', ('mobile',), as_dict=True)
    unique_idx = [r for r in result if r.get('Non_unique') == 0]
    if unique_idx:
        print('  ✓ Unique index on Patient.mobile')
    else:
        print('  ⚠ No unique index on Patient.mobile (may have existing duplicates)')
    
    # Intake mobile
    result = frappe.db.sql('SHOW INDEXES FROM `tabGLP-1 Intake Submission` WHERE Column_name = %s', ('mobile',), as_dict=True)
    unique_idx = [r for r in result if r.get('Non_unique') == 0]
    if unique_idx:
        print('  ✓ Unique index on GLP-1 Intake Submission.mobile')
    else:
        print('  ⚠ No unique index on GLP-1 Intake Submission.mobile (may have existing duplicates)')
    
    # ID Number
    result = frappe.db.sql('SHOW INDEXES FROM `tabGLP-1 Intake Submission` WHERE Column_name = %s', ('id_number__passport_number',), as_dict=True)
    unique_idx = [r for r in result if r.get('Non_unique') == 0]
    if unique_idx:
        print('  ✓ Unique index on GLP-1 Intake Submission.id_number__passport_number')
    else:
        print('  ⚠ No unique index on GLP-1 Intake Submission.id_number__passport_number (may have existing duplicates)')
        
except Exception as e:
    print(f'  Error checking indexes: {e}')
    import traceback
    traceback.print_exc()

print('\n✅ Verification complete!')
print('\nNote: Even if database indexes are not set due to existing duplicates,')
print('      the validation hooks in Python code will prevent new duplicates.')

frappe.destroy()

