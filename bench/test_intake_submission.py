#!/usr/bin/env python3
"""Test script to verify intake form submission and after_insert hook"""
import sys
sys.path.insert(0, 'apps')
import os
os.chdir('sites')
import frappe

frappe.init(site='koraflow-site')
frappe.connect()

# Set session to the test user
frappe.set_user('johnpatient1735512345@example.com')

print('=' * 60)
print('TESTING INTAKE FORM SUBMISSION')
print('=' * 60)
print(f'User: {frappe.session.user}')
print()

# Get Gender value
gender = frappe.db.get_value('Gender', {'name': 'Male'}, 'name')
if not gender:
    # Try to get any gender
    gender = frappe.db.get_value('Gender', {}, 'name')
    if not gender:
        print('⚠ No Gender found, using "Male" as string')
        gender = 'Male'

print(f'Using Gender: {gender}')
print()

# Create a minimal valid intake submission
intake_data = {
    'doctype': 'GLP-1 Intake Submission',
    'first_name': 'John',
    'last_name': 'Test Patient',
    'dob': '1985-01-15',
    'sex': gender,
    'email': 'johnpatient1735512345@example.com',
    'mobile': '555-123-4567',
    'intake_height_unit': 'Feet/Inches',
    'intake_height_feet': 5,
    'intake_height_inches': 10,
    'intake_height_cm': 177.8,
    'intake_weight_unit': 'Pounds',
    'intake_weight_pounds': 180,
    'intake_weight_kg': 81.6,
    'intake_bp_systolic': 120,
    'intake_bp_diastolic': 80,
    'intake_heart_rate': 72,
}

print('Creating intake submission...')
try:
    submission = frappe.get_doc(intake_data)
    submission.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f'✓ Created submission: {submission.name}')
    print()
    
    # Check if patient was updated
    patient = frappe.db.get_value('Patient', {'email': 'johnpatient1735512345@example.com'}, 'name')
    if patient:
        patient_doc = frappe.get_doc('Patient', patient)
        print(f'✓ Patient: {patient}')
        print(f'  Status: {patient_doc.status}')
        print(f'  Intake forms in child table: {len(patient_doc.glp1_intake_forms)}')
        print()
        
        if len(patient_doc.glp1_intake_forms) > 0:
            print('  ✓ SUCCESS: Intake form created in child table!')
            for intake in patient_doc.glp1_intake_forms:
                print(f'    - {intake.name}: {intake.first_name} {intake.last_name}')
        else:
            print('  ✗ FAILED: No intake forms in child table')
            print('  This means the after_insert hook did not run or failed')
            print()
            print('  Checking error logs...')
            errors = frappe.get_all('Error Log',
                filters={'error': ['like', '%intake%']},
                fields=['name', 'creation'],
                order_by='creation desc',
                limit=3)
            for err in errors:
                err_doc = frappe.get_doc('Error Log', err.name)
                print(f'    Error {err.name}: {err_doc.error[:200]}...')
    else:
        print('✗ Patient not found')
        
except Exception as e:
    print(f'✗ Error creating submission: {e}')
    import traceback
    traceback.print_exc()

frappe.destroy()

