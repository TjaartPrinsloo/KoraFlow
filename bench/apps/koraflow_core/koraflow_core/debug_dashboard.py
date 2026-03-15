import frappe

def debug_dashboard_context():
    from koraflow_core.www.dashboard import get_context
    # 1. Create a dummy patient with "Disabled" status and No Intake
    user_email = "new.patient.v3@example.com"
    if not frappe.db.exists("User", user_email):
        user = frappe.new_doc("User")
        user.email = user_email
        user.first_name = "New"
        user.last_name = "Patient V3"
        user.insert(ignore_permissions=True)
        
    patient_name = frappe.db.get_value("Patient", {"email": user_email}, "name")
    if not patient_name:
        p = frappe.new_doc("Patient")
        p.first_name = "New"
        p.last_name = "Patient V3"
        p.email = user_email
        p.status = "Disabled" # Simulate new/under review
        p.flags.ignore_permissions = True
        p.flags.ignore_mandatory = True
        p.insert(ignore_permissions=True)
        patient_name = p.name

    else:
        p = frappe.get_doc("Patient", patient_name)
        p.status = "Disabled"
        p.save(ignore_permissions=True)
        
    # Ensure no intake
    frappe.db.sql("DELETE FROM `tabGLP-1 Intake Submission` WHERE parent = %s", patient_name)
    frappe.db.commit()

    # Mock Setup for Context
    class MockContext(dict):
        def __init__(self):
            self.no_cache = 0

    context = MockContext()
    
    # Mock Session
    frappe.session.user = user_email
    
    # Run get_context
    try:
        get_context(context)
        print(f"DEBUG: Patient: {patient_name}, Status: {p.status}")
        print(f"DEBUG: Intake Completed: {context.get('intake_completed')}")
        print(f"DEBUG: Refill Info: {context.get('refill_info')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

debug_dashboard_context()
