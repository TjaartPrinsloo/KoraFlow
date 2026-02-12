
import frappe
import json
from frappe.utils import getdate

# Explicitly set path to sites
sites_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/sites"

def test_dashboard_context(user_email):
    print(f"\n--- Testing Dashboard for: {user_email} ---")
    
    # Mock session
    if not hasattr(frappe, 'session'):
        frappe.session = frappe._dict({'user': user_email})
    else:
        frappe.session.user = user_email
    
    # Mock roles
    frappe.get_roles = lambda x=None: ["Patient", "Website User"]
    
    # Mock context
    context = frappe._dict()
    
    # Import function directly to test logic
    try:
        import sys
        if 'koraflow_core.www.patient_dashboard' in sys.modules:
            del sys.modules['koraflow_core.www.patient_dashboard']
            
        from koraflow_core.www.patient_dashboard import get_context
        get_context(context)
        
        print(f"Patient Status: {context.patient.status if context.patient else 'None'}")
        
        if context.latest_vital:
            print(f"Latest Vital (Weight): {context.latest_vital.get('weight_kg')}")
            print(f"Latest Vital (BMI): {context.latest_vital.get('bmi')}")
            print(f"BMI Class: {context.bmi_class}")
            print(f"Target Weight: {context.target_weight}")
            print(f"Chart Data Points: {len(context.vitals_history) if context.vitals_history else 0}")
            if context.vitals_history:
                 print(f"First Chart Point: {context.vitals_history[0]}")
            
            print(f"Latest Vital Source Date: {context.latest_vital.get('date')}")
        else:
            print("Latest Vital: None")
            
        print(f"Show Medical Auth: {context.show_medical_auth}")
        print(f"Show Billing: {context.show_billing}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    frappe.init(site="koraflow-site", sites_path=sites_path)
    frappe.connect()
    
    # Create dummy intake form if needed for testing fallback
    user_email = "patient0@example.com"
    patient = frappe.db.get_value("Patient", {"email": user_email}, "name")
    # Create Patient if missing
    if not patient:
        print("Creating dummy Patient...")
        patient_doc = frappe.get_doc({
            "doctype": "Patient",
            "first_name": "Patient",
            "last_name": "Zero",
            "email": user_email,
            "sex": "Male",
            "status": "Disabled",
            "invite_user": 0
        })
        # Mock user link
        if frappe.db.exists("User", user_email):
           patient_doc.user_id = user_email
        patient_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        patient = patient_doc.name
    
    # Delete any existing vitals to force fallback
    frappe.db.delete("Patient Vital", {"patient": patient})
    frappe.db.commit()
    
    print(f"DEBUG: user_email={user_email}, patient={patient}")
    if patient:
        print("Forcing creation of dummy intake submission...")
        doc = frappe.get_doc({
            "doctype": "GLP-1 Intake Submission",
            "parent": patient,
            "parenttype": "Patient",
            "parentfield": "glp1_intake_forms",
            "intake_weight_kg": 95.5,
            "intake_height_cm": 180,
            "email": user_email,
            "intake_goal_weight": 80.0,
            "first_name": "Patient",
            "last_name": "Zero",
            "dob": "1990-01-01",
            "sex": "Male",
            "intake_height_unit": "Centimeters",
            "intake_weight_unit": "Kilograms"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    
    # Check if we can find it
    print(f"DEBUG Check: {frappe.get_all('GLP-1 Intake Submission', filters={'parent': patient})}")

    # Test Patient0 (New user, should have intake but no vitals, status Disabled/Under Review)
    test_dashboard_context(user_email) 
