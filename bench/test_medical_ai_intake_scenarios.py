#!/usr/bin/env python3
"""
Comprehensive Unit Test for Medical AI Intake Form with Real-World Scenarios

This test script creates multiple realistic patient scenarios to test:
1. Intake form submission
2. Patient record creation
3. AI medical summary generation
4. Various medical conditions and contraindications
"""

import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, 'apps')
os.chdir('sites')
import frappe

frappe.init(site='koraflow-site')
frappe.connect()

# Set to Administrator for testing
frappe.set_user('Administrator')

print('=' * 80)
print('MEDICAL AI INTAKE FORM - REAL-WORLD SCENARIO TESTING')
print('=' * 80)
print()


def get_gender():
    """Get a valid Gender from the database"""
    gender = frappe.db.get_value('Gender', {'name': 'Male'}, 'name')
    if not gender:
        gender = frappe.db.get_value('Gender', {}, 'name')
    if not gender:
        gender = 'Male'  # Fallback
    return gender


def generate_unique_email(base_name):
    """Generate unique email for testing"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{base_name.lower().replace(' ', '')}{timestamp}@test.example.com"


def generate_unique_mobile():
    """Generate unique mobile number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"555-{timestamp[-7:-4]}-{timestamp[-4:]}"


def generate_unique_id():
    """Generate unique ID number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"ID{timestamp}"


# Real-world test scenarios
TEST_SCENARIOS = [
    {
        "name": "Healthy Patient - Ideal Candidate",
        "description": "Young, healthy patient with no contraindications",
        "data": {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "dob": "1990-05-15",
            "sex": None,  # Will be set
            "email": None,  # Will be generated
            "mobile": None,  # Will be generated
            "id_number__passport_number": None,  # Will be generated
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 5,
            "intake_height_inches": 6,
            "intake_height_cm": 167.6,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 180,
            "intake_weight_kg": 81.6,
            "intake_bp_systolic": 118,
            "intake_bp_diastolic": 75,
            "intake_heart_rate": 68,
            # No high-risk conditions
            "intake_mtc": 0,
            "intake_men2": 0,
            "intake_pancreatitis": 0,
            "intake_gallstones": 0,
            "intake_gallbladder_removal": 0,
            "intake_gastroparesis": 0,
            "intake_frequent_nausea": 0,
            "intake_early_fullness": 0,
            # No organ system issues
            "intake_kidney_disease": 0,
            "intake_diabetic_retinopathy": 0,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 0,
            # No medications
            "intake_taking_insulin": 0,
            "intake_taking_sulfonylureas": 0,
            "intake_narrow_window_drugs": 0,
            # No GLP-1 history
            "intake_med_ozempic": 0,
            "intake_med_wegovy": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # No side effects
            "intake_se_nausea": 0,
            "intake_se_vomiting": 0,
            "intake_se_diarrhea": 0,
            "intake_se_constipation": 0,
            "intake_se_reflux": 0,
            # Reproductive
            "intake_pregnant": 0,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 0,
        }
    },
    {
        "name": "Patient with Contraindications - Pancreatitis History",
        "description": "Patient with history of pancreatitis (contraindication)",
        "data": {
            "first_name": "Michael",
            "last_name": "Chen",
            "dob": "1975-08-22",
            "sex": None,
            "email": None,
            "mobile": None,
            "id_number__passport_number": None,
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 5,
            "intake_height_inches": 10,
            "intake_height_cm": 177.8,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 220,
            "intake_weight_kg": 99.8,
            "intake_bp_systolic": 130,
            "intake_bp_diastolic": 85,
            "intake_heart_rate": 78,
            # HIGH RISK: Pancreatitis
            "intake_pancreatitis": 1,
            "intake_gallstones": 1,
            "intake_gallbladder_removal": 1,
            "intake_mtc": 0,
            "intake_men2": 0,
            "intake_gastroparesis": 0,
            "intake_frequent_nausea": 1,
            "intake_early_fullness": 1,
            # Organ systems
            "intake_kidney_disease": 0,
            "intake_diabetic_retinopathy": 0,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 0,
            # Medications
            "intake_taking_insulin": 0,
            "intake_taking_sulfonylureas": 0,
            "intake_narrow_window_drugs": 0,
            # GLP-1 history
            "intake_med_ozempic": 0,
            "intake_med_wegovy": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # Side effects
            "intake_se_nausea": 0,
            "intake_se_vomiting": 0,
            "intake_se_diarrhea": 0,
            "intake_se_constipation": 0,
            "intake_se_reflux": 0,
            # Reproductive
            "intake_pregnant": 0,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 0,
        }
    },
    {
        "name": "Patient with Kidney Disease - eGFR Monitoring Required",
        "description": "Patient with kidney disease requiring careful monitoring",
        "data": {
            "first_name": "Robert",
            "last_name": "Williams",
            "dob": "1965-03-10",
            "sex": None,
            "email": None,
            "mobile": None,
            "id_number__passport_number": None,
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 6,
            "intake_height_inches": 0,
            "intake_height_cm": 182.9,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 250,
            "intake_weight_kg": 113.4,
            "intake_bp_systolic": 140,
            "intake_bp_diastolic": 90,
            "intake_heart_rate": 82,
            # High risk
            "intake_mtc": 0,
            "intake_men2": 0,
            "intake_pancreatitis": 0,
            "intake_gallstones": 0,
            "intake_gallbladder_removal": 0,
            "intake_gastroparesis": 0,
            "intake_frequent_nausea": 0,
            "intake_early_fullness": 0,
            # ORGAN SYSTEM: Kidney disease
            "intake_kidney_disease": 1,
            "intake_egfr": 45.5,
            "intake_creatinine": 1.8,
            "intake_diabetic_retinopathy": 1,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 1,
            # Medications
            "intake_taking_insulin": 1,
            "intake_insulin_dose": "20 units daily",
            "intake_taking_sulfonylureas": 0,
            "intake_narrow_window_drugs": 1,
            # GLP-1 history
            "intake_med_ozempic": 1,
            "intake_highest_dose": "1.0 mg",
            "intake_last_dose_date": "2024-06-15",
            "intake_med_wegovy": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # Side effects from previous use
            "intake_se_nausea": 1,
            "intake_se_vomiting": 0,
            "intake_se_diarrhea": 1,
            "intake_se_constipation": 0,
            "intake_se_reflux": 1,
            "intake_se_severity": "Moderate",
            # Reproductive
            "intake_pregnant": 0,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 0,
        }
    },
    {
        "name": "Pregnant Patient - Absolute Contraindication",
        "description": "Pregnant patient (absolute contraindication for GLP-1)",
        "data": {
            "first_name": "Emily",
            "last_name": "Davis",
            "dob": "1992-11-20",
            "sex": None,
            "email": None,
            "mobile": None,
            "id_number__passport_number": None,
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 5,
            "intake_height_inches": 4,
            "intake_height_cm": 162.6,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 165,
            "intake_weight_kg": 74.8,
            "intake_bp_systolic": 115,
            "intake_bp_diastolic": 70,
            "intake_heart_rate": 72,
            # High risk
            "intake_mtc": 0,
            "intake_men2": 0,
            "intake_pancreatitis": 0,
            "intake_gallstones": 0,
            "intake_gallbladder_removal": 0,
            "intake_gastroparesis": 0,
            "intake_frequent_nausea": 1,  # Common in pregnancy
            "intake_early_fullness": 1,
            # Organ systems
            "intake_kidney_disease": 0,
            "intake_diabetic_retinopathy": 0,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 0,
            # Medications
            "intake_taking_insulin": 0,
            "intake_taking_sulfonylureas": 0,
            "intake_narrow_window_drugs": 0,
            # GLP-1 history
            "intake_med_ozempic": 0,
            "intake_med_wegovy": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # Side effects
            "intake_se_nausea": 0,
            "intake_se_vomiting": 0,
            "intake_se_diarrhea": 0,
            "intake_se_constipation": 0,
            "intake_se_reflux": 0,
            # REPRODUCTIVE: Pregnant
            "intake_pregnant": 1,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 0,
        }
    },
    {
        "name": "Patient with MTC/MEN2 - Absolute Contraindication",
        "description": "Patient with medullary thyroid carcinoma history (absolute contraindication)",
        "data": {
            "first_name": "David",
            "last_name": "Martinez",
            "dob": "1980-07-05",
            "sex": None,
            "email": None,
            "mobile": None,
            "id_number__passport_number": None,
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 5,
            "intake_height_inches": 11,
            "intake_height_cm": 180.3,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 200,
            "intake_weight_kg": 90.7,
            "intake_bp_systolic": 125,
            "intake_bp_diastolic": 80,
            "intake_heart_rate": 70,
            # HIGH RISK: MTC/MEN2 (absolute contraindication)
            "intake_mtc": 1,
            "intake_men2": 1,
            "intake_pancreatitis": 0,
            "intake_gallstones": 0,
            "intake_gallbladder_removal": 0,
            "intake_gastroparesis": 0,
            "intake_frequent_nausea": 0,
            "intake_early_fullness": 0,
            # Organ systems
            "intake_kidney_disease": 0,
            "intake_diabetic_retinopathy": 0,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 0,
            # Medications
            "intake_taking_insulin": 0,
            "intake_taking_sulfonylureas": 0,
            "intake_narrow_window_drugs": 0,
            # GLP-1 history
            "intake_med_ozempic": 0,
            "intake_med_wegovy": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # Side effects
            "intake_se_nausea": 0,
            "intake_se_vomiting": 0,
            "intake_se_diarrhea": 0,
            "intake_se_constipation": 0,
            "intake_se_reflux": 0,
            # Reproductive
            "intake_pregnant": 0,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 0,
        }
    },
    {
        "name": "Patient with Previous GLP-1 Experience - Side Effects",
        "description": "Patient who previously used GLP-1 with significant side effects",
        "data": {
            "first_name": "Jennifer",
            "last_name": "Anderson",
            "dob": "1988-12-03",
            "sex": None,
            "email": None,
            "mobile": None,
            "id_number__passport_number": None,
            "intake_height_unit": "Feet/Inches",
            "intake_height_feet": 5,
            "intake_height_inches": 5,
            "intake_height_cm": 165.1,
            "intake_weight_unit": "Pounds",
            "intake_weight_pounds": 190,
            "intake_weight_kg": 86.2,
            "intake_bp_systolic": 122,
            "intake_bp_diastolic": 78,
            "intake_heart_rate": 74,
            # High risk
            "intake_mtc": 0,
            "intake_men2": 0,
            "intake_pancreatitis": 0,
            "intake_gallstones": 0,
            "intake_gallbladder_removal": 0,
            "intake_gastroparesis": 1,  # Developed after GLP-1 use
            "intake_frequent_nausea": 1,
            "intake_early_fullness": 1,
            # Organ systems
            "intake_kidney_disease": 0,
            "intake_diabetic_retinopathy": 0,
            "intake_heart_attack": 0,
            "intake_stroke": 0,
            "intake_heart_failure": 0,
            # Medications
            "intake_taking_insulin": 0,
            "intake_taking_sulfonylureas": 1,
            "intake_narrow_window_drugs": 0,
            # GLP-1 HISTORY: Previous use with side effects
            "intake_med_wegovy": 1,
            "intake_highest_dose": "2.4 mg",
            "intake_last_dose_date": "2024-03-20",
            "intake_med_ozempic": 0,
            "intake_med_mounjaro": 0,
            "intake_med_zepbound": 0,
            # SIDE EFFECTS: Significant
            "intake_se_nausea": 1,
            "intake_se_vomiting": 1,
            "intake_se_diarrhea": 1,
            "intake_se_constipation": 1,
            "intake_se_reflux": 1,
            "intake_se_severity": "Severe",
            # Reproductive
            "intake_pregnant": 0,
            "intake_breastfeeding": 0,
            "intake_planning_conceive": 1,  # Planning pregnancy
        }
    },
]


def test_scenario(scenario):
    """Test a single scenario"""
    print(f"Testing: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print("-" * 80)
    
    # Prepare data
    data = scenario['data'].copy()
    gender = get_gender()
    data['sex'] = gender
    data['email'] = generate_unique_email(f"{data['first_name']} {data['last_name']}")
    data['mobile'] = generate_unique_mobile()
    data['id_number__passport_number'] = generate_unique_id()
    data['doctype'] = 'GLP-1 Intake Submission'
    
    try:
        # Create user via SQL to bypass hooks
        if not frappe.db.exists("User", data['email']):
            frappe.db.sql("""
                INSERT INTO `tabUser` (name, email, first_name, last_name, enabled, user_type, creation, modified, modified_by, owner)
                VALUES (%s, %s, %s, %s, 1, 'Patient', NOW(), NOW(), 'Administrator', 'Administrator')
            """, (data['email'], data['email'], data['first_name'], data['last_name']))
            
            # Add Patient role
            if not frappe.db.exists("Has Role", {"parent": data['email'], "role": "Patient"}):
                frappe.get_doc({
                    "doctype": "Has Role",
                    "parent": data['email'],
                    "parenttype": "User",
                    "role": "Patient"
                }).insert(ignore_permissions=True)
            
            frappe.db.commit()
            print(f"  ✓ Created user: {data['email']}")
        
        # Use the API method directly
        from koraflow_core.api.patient_signup import create_patient_from_intake
        
        # Set user session to the test user for API call
        frappe.set_user(data['email'])
        
        # Call the API method that handles everything
        result = create_patient_from_intake(data, user_email=data['email'])
        
        if not result.get('success'):
            print(f"  ✗ API call failed: {result.get('message', 'Unknown error')}")
            return {"success": False, "error": result.get('message', 'API call failed')}
        
        print(f"  ✓ Created patient: {result.get('patient')}")
        print(f"  ✓ Created intake form: {result.get('intake_form')}")
        
        # Check patient record
        patient_name = result.get('patient')
        if patient_name:
            patient_doc = frappe.get_doc('Patient', patient_name)
            print(f"  ✓ Patient record: {patient_name}")
            print(f"    Status: {patient_doc.status}")
            print(f"    Intake forms: {len(patient_doc.glp1_intake_forms)}")
            
            # Check for AI medical summary
            if hasattr(patient_doc, 'ai_medical_summary') and patient_doc.ai_medical_summary:
                summary_length = len(patient_doc.ai_medical_summary)
                print(f"    ✓ AI Medical Summary: Generated ({summary_length} characters)")
                print(f"    Preview: {patient_doc.ai_medical_summary[:200]}...")
            else:
                print(f"    ⚠ AI Medical Summary: Not generated (check Ollama service)")
            
            return {
                "success": True,
                "patient": patient_name,
                "submission": result.get('intake_form'),
                "has_summary": bool(hasattr(patient_doc, 'ai_medical_summary') and patient_doc.ai_medical_summary)
            }
        else:
            print(f"  ✗ Patient record not found")
            return {"success": False, "error": "Patient not created"}
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """Run all test scenarios"""
    results = []
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n[{i}/{len(TEST_SCENARIOS)}]")
        result = test_scenario(scenario)
        result['scenario'] = scenario['name']
        results.append(result)
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in results if r.get('success'))
    total = len(results)
    
    print(f"Total Scenarios: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print()
    
    summaries_generated = sum(1 for r in results if r.get('has_summary'))
    print(f"AI Medical Summaries Generated: {summaries_generated}/{total}")
    print()
    
    print("Detailed Results:")
    for i, result in enumerate(results, 1):
        status = "✓" if result.get('success') else "✗"
        summary_status = "✓" if result.get('has_summary') else "✗"
        print(f"  {status} [{i}] {result['scenario']} - Summary: {summary_status}")
    
    print()
    print("=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    finally:
        frappe.destroy()

