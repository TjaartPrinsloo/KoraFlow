import frappe
from frappe import _
import sys
import traceback

def debug():
    try:
        frappe.connect()
        
        # Get latest patient
        patient = frappe.get_all("Patient", order_by="creation desc", limit=1)
        if not patient:
            print("No patients found")
            return
            
        p_name = patient[0].name
        p_email = frappe.db.get_value("Patient", p_name, "email")
        print(f"Testing for Patient: {p_name} ({p_email})")
        
        # Mock session
        frappe.session.user = p_email
        frappe.local.flags.redirect_location = None
        
        # Mock context
        context = frappe._dict()
        
        # Import and run
        from koraflow_core.www import patient_dashboard
        try:
            patient_dashboard.get_context(context)
            print("Success! Context keys:", context.keys())
        except frappe.Redirect:
            print(f"Redirected to: {frappe.local.flags.redirect_location}")
        except Exception:
            traceback.print_exc()

    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    frappe.init('koraflow-site', sites_path='sites')
    debug()
