import frappe
import traceback
import sys

def debug():
    try:
        # Get a test user (patient)
        user = frappe.db.get_value("User", {"email": "test_user_67890@koraflow.com"}, "name")
        if not user:
            # Fallback to any patient
            user = frappe.db.get_value("Patient", {}, "email")
            
        print(f"Testing Billing for User: {user}")
        
        # Mock session
        frappe.session.user = user
        frappe.local.flags.redirect_location = None
        
        # Mock context
        context = frappe._dict()
        
        # Import and run
        from koraflow_core.www import billing
        try:
            billing.get_context(context)
            print("Success! Context keys:", context.keys())
        except frappe.Redirect:
            print(f"Redirected to: {frappe.local.flags.redirect_location}")
        except Exception:
            traceback.print_exc()

    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    frappe.init("koraflow-site", sites_path="sites")
    frappe.connect()
    debug()
