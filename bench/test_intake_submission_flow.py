#!/usr/bin/env python3
"""
Test script to verify complete intake submission flow:
1. User signup
2. Intake form submission
3. Medical summary generation
4. Intake completed flag
5. Patient record creation
"""

import frappe
import sys
import traceback
from datetime import datetime

def test_intake_submission_flow():
    """Test the complete intake submission flow"""
    print("=" * 80)
    print("TESTING INTAKE SUBMISSION FLOW")
    print("=" * 80)
    
    # Generate unique test email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"test.intake.{timestamp}@test.com"
    test_name = f"Test Patient {timestamp}"
    
    print(f"\n1. Creating test user: {test_email}")
    print("-" * 80)
    
    try:
        # Create test user
        from koraflow_core.api.patient_signup import patient_sign_up
        
        result = patient_sign_up(
            email=test_email,
            full_name=test_name,
            redirect_to="/glp1-intake"
        )
        
        status, message = result
        if status == 1 or status == 2:  # Status 2 = created but email failed (OK for testing)
            print(f"✓ User created successfully")
            print(f"  Message: {message}")
            if status == 2:
                print(f"  Note: Email sending failed (OK for testing)")
        else:
            print(f"✗ User creation failed: {message}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating user: {str(e)}")
        traceback.print_exc()
        return False
    
    # Verify user was created
    if not frappe.db.exists("User", test_email):
        print(f"✗ User {test_email} was not created")
        return False
    
    user = frappe.get_doc("User", test_email)
    print(f"✓ User exists: {user.name}")
    print(f"  Email Verified: {user.email_verified}")
    print(f"  Intake Completed: {user.intake_completed}")
    
    # Force verify email for testing (simulate email verification)
    print(f"\n2. Force verifying email (for testing)")
    print("-" * 80)
    try:
        from koraflow_core.api.patient_signup import force_verify_email
        frappe.set_user("Administrator")
        force_verify_email(test_email, reason="Test verification")
        frappe.set_user("Guest")
        
        user.reload()
        if user.email_verified:
            print(f"✓ Email verified successfully")
        else:
            print(f"✗ Email verification failed")
            return False
    except Exception as e:
        print(f"✗ Error verifying email: {str(e)}")
        traceback.print_exc()
        return False
    
    # Create a mock intake form document
    print(f"\n3. Creating intake form submission")
    print("-" * 80)
    
    # Get GLP-1 Intake Submission meta to know what fields to include
    submission_meta = frappe.get_meta("GLP-1 Intake Submission")
    valid_fields = [f.fieldname for f in submission_meta.fields 
                   if f.fieldtype not in ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button']]
    
    # Create mock intake data
    intake_data = {
        "email": test_email,
        "first_name": test_name.split()[0],
        "last_name": " ".join(test_name.split()[1:]) if len(test_name.split()) > 1 else "Patient",
        "mobile": f"555{timestamp[-6:]}",
        "dob": "1990-01-01",
        "sex": "Male",
        "height": "70",
        "weight": "180",
        "medical_history": "Diabetes, Hypertension",
        "current_medications": "Metformin, Lisinopril",
        "allergies": "None",
    }
    
    # Add any other required fields
    for field in valid_fields[:20]:  # Limit to first 20 fields
        if field not in intake_data and field not in ["name", "owner", "creation", "modified"]:
            # Set default values based on field type
            field_obj = submission_meta.get_field(field)
            if field_obj:
                if field_obj.fieldtype == "Check":
                    intake_data[field] = 0
                elif field_obj.fieldtype == "Int":
                    intake_data[field] = 0
                elif field_obj.fieldtype == "Float":
                    intake_data[field] = 0.0
    
    # Create a mock Document object
    class MockIntakeDoc:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    mock_doc = MockIntakeDoc(intake_data)
    
    # Process intake submission
    try:
        from koraflow_core.api.patient_signup import process_intake_submission_from_web_form
        
        # Set user context
        frappe.set_user(test_email)
        
        result = process_intake_submission_from_web_form(mock_doc, test_email)
        
        if result and result.get("success"):
            print(f"✓ Intake form submitted successfully")
            print(f"  Patient: {result.get('patient')}")
            print(f"  Intake Form: {result.get('intake_form_name')}")
            print(f"  Status: {result.get('status')}")
        else:
            print(f"✗ Intake submission failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Error submitting intake form: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        frappe.set_user("Administrator")
    
    # Verify results
    print(f"\n4. Verifying results")
    print("-" * 80)
    
    # Check user intake_completed flag
    user.reload()
    if user.intake_completed:
        print(f"✓ User intake_completed flag is set to 1")
    else:
        print(f"✗ User intake_completed flag is NOT set (value: {user.intake_completed})")
        return False
    
    # Check patient exists
    patient_name = frappe.db.get_value("Patient", {"email": test_email}, "name")
    if patient_name:
        print(f"✓ Patient record exists: {patient_name}")
        patient = frappe.get_doc("Patient", patient_name)
        
        # Check intake forms
        if patient.glp1_intake_forms:
            print(f"✓ Patient has {len(patient.glp1_intake_forms)} intake form(s)")
            for idx, form in enumerate(patient.glp1_intake_forms):
                print(f"  Form {idx+1}: {form.name}")
        else:
            print(f"✗ Patient has NO intake forms")
            return False
        
        # Check medical summary
        if patient.ai_medical_summary:
            summary_length = len(patient.ai_medical_summary)
            print(f"✓ Medical summary generated ({summary_length} characters)")
            print(f"  Preview: {patient.ai_medical_summary[:200]}...")
        else:
            print(f"✗ Medical summary NOT generated")
            # Check error logs
            errors = frappe.get_all("Error Log",
                filters={"error": ["like", "%medical%"]},
                order_by="creation desc",
                limit=1
            )
            if errors:
                err = frappe.get_doc("Error Log", errors[0].name)
                print(f"  Error: {err.error[:300]}...")
            return False
    else:
        print(f"✗ Patient record NOT found")
        return False
    
    print(f"\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    # Initialize Frappe
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        success = test_intake_submission_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        frappe.destroy()

