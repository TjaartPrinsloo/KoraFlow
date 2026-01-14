#!/usr/bin/env python3
"""
Create a test referral for testing the system
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
    print("Creating test referral...")
    
    # Get a sales partner
    sales_partners = frappe.get_all("Sales Partner", fields=["name"], limit=1)
    if not sales_partners:
        print("  ❌ No Sales Partners found")
        exit(1)
    
    sales_partner = sales_partners[0].name
    print(f"  Using Sales Partner: {sales_partner}")
    
    # Get a patient
    patients = frappe.get_all("Patient", fields=["name", "first_name", "last_name"], limit=1)
    if not patients:
        print("  ❌ No Patients found")
        exit(1)
    
    patient = patients[0]
    print(f"  Using Patient: {patient.name} ({patient.first_name} {patient.last_name})")
    
    # Create referral
    referral = frappe.get_doc({
        "doctype": "Sales Partner Referral",
        "sales_partner": sales_partner,
        "patient": patient.name,
        "first_name": patient.first_name or "Test",
        "last_name": patient.last_name or "Patient",
        "referral_date": frappe.utils.today(),
        "referral_status": "Quotation Pending"
    })
    
    referral.flags.ignore_permissions = True
    referral.insert()
    frappe.db.commit()
    
    print(f"  ✓ Created referral: {referral.name}")
    print(f"  Access at: /my-referrals/{referral.name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

