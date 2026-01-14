import sys
import os
import time

sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from koraflow_core.api.medical_summary import generate_medical_summary

def test_determinism():
    print("================================================================================")
    print("RAG DETERMINISM TEST")
    print("================================================================================")
    
    # Complex patient data to challenge the model
    intake_data = {
        'first_name': 'Test',
        'last_name': 'Determinism',
        'dob': '1980-01-01',
        'sex': 'Female',
        'intake_height_feet': '5',
        'intake_height_inches': '6',
        'intake_weight_pounds': '180',
        'intake_mtc': 1, # High risk
        'intake_kidney_disease': 1,
        'intake_egfr': '45',
        'intake_med_ozempic': 1,
        'intake_highest_dose': '1mg',
        'intake_se_nausea': 1
    }
    
    patient_name = "TEST-DETERMINISM-001"
    
    print("\nGenerating Summary 1...")
    s1 = generate_medical_summary(intake_data, patient_name)
    print(f"Length: {len(s1) if s1 else 0} chars")
    
    print("\nGenerating Summary 2...")
    s2 = generate_medical_summary(intake_data, patient_name)
    print(f"Length: {len(s2) if s2 else 0} chars")
    
    print("\nGenerating Summary 3...")
    s3 = generate_medical_summary(intake_data, patient_name)
    print(f"Length: {len(s3) if s3 else 0} chars")
    
    if not s1 or not s2 or not s3:
        print("\n[FAIL] One or more summaries failed to generate.")
        return

    # Check for exact string equality
    if s1 == s2 == s3:
        print("\n[PASS] Determinism Achieved! All 3 summaries are identical.")
        print("-" * 40)
        print(s1)
        print("-" * 40)
    else:
        print("\n[FAIL] Summaries passed are NOT identical.")
        if s1 != s2: print("s1 != s2")
        if s2 != s3: print("s2 != s3")
        if s1 != s3: print("s1 != s3")

if __name__ == "__main__":
    frappe.init(site="koraflow-site")
    frappe.connect()
    test_determinism()
