import sys
import os

# Set up Frappe environment
sys.path.append("..")
from frappe.utils.bench_helper import get_app_groups

apps_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps"
sites_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/sites"

sys.path.insert(0, os.path.join(apps_path, "frappe"))
sys.path.insert(0, os.path.join(apps_path, "koraflow_core"))

import frappe
from frappe.utils import get_site_name

def init_site(site):
    frappe.init(site=site, sites_path=sites_path)
    frappe.connect()

def debug_dashboard_context():
    init_site("koraflow-site")
    
    from koraflow_core.www.dashboard import get_context
    
    try:
        # 1. Create a dummy patient with "Disabled" status and No Intake
        user_email = "new.patient.v4@example.com"
        if not frappe.db.exists("User", user_email):
            print(f"Creating user {user_email}...")
            user = frappe.new_doc("User")
            user.email = user_email
            user.first_name = "New"
            user.last_name = "Patient V4"
            user.insert(ignore_permissions=True)
            
        patient_name = frappe.db.get_value("Patient", {"email": user_email}, "name")
        if not patient_name:
            print("Creating Patient...")
            p = frappe.new_doc("Patient")
            p.first_name = "New"
            p.last_name = "Patient V4"
            p.email = user_email
            p.status = "Disabled" # Simulate new/under review
            p.flags.ignore_permissions = True
            p.flags.ignore_mandatory = True
            p.name = "Patient-New-V4"
            p.db_insert() 
            patient_name = p.name
        else:
            print(f"Found Patient: {patient_name}")
            p = frappe.get_doc("Patient", patient_name)
            frappe.db.set_value("Patient", patient_name, "status", "Disabled")
            frappe.db.commit()
            
        # Create dummy intake submission to make intake_completed = True
        if not frappe.db.exists("GLP-1 Intake Submission", {"parent": patient_name}):
            doc = frappe.new_doc("GLP-1 Intake Submission")
            doc.parent = patient_name
            doc.parenttype = "Patient"
            doc.parentfield = "intake_forms"
            doc.first_name = "New"
            doc.last_name = "Patient V4"
            doc.dob = "1990-01-01"
            doc.sex = "Male"
            doc.intake_height_unit = "Centimeters"
            doc.intake_weight_unit = "Kilograms"
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

        # Mock Setup for Context
        class MockContext(dict):
            def __init__(self):
                self.no_cache = 0

        context = MockContext()
        
        # Mock Session
        frappe.session.user = user_email
        
        frappe.db.set_value("Patient", patient_name, "status", "Active")
        frappe.db.commit()
        # Reload to ensure object is fresh if needed, but we care about DB
        p.reload()
        
        get_context(context)
        print(f"DEBUG: Patient: {patient_name}, Status: {p.status}")
        print(f"DEBUG: Intake Completed: {context.get('intake_completed')}")
        print(f"DEBUG: Refill Info: {context.get('refill_info')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frappe.destroy()

if __name__ == "__main__":
    debug_dashboard_context()
