
import frappe
from frappe import _
from frappe.utils import set_request
import os

# Explicitly set path to sites
sites_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/sites"

class MockLoginManager:
    def __init__(self, user):
        self.user = user

def verify_redirect_logic(user_email, expected_route):
    print(f"\n--- Testing User: {user_email} ---")
    user_name = frappe.db.get_value("User", {"email": user_email}, "name")
    
    if not user_name:
        print(f"User {user_email} not found.")
        return

    # Mock LoginManager
    login_manager = MockLoginManager(user_name)
    
    # Mock frappe.local.response
    frappe.local.response = {}
    
    # Run mock logic (copy-pasted because we can't easily import the function if it's not in path properly or needs context)
    # Ideally we import, but let's test the logic flow against the DB values directly first to confirm data state
    
    user = login_manager.user
    roles = frappe.get_roles(user)
    print(f"Roles: {roles}")
    
    user_type = frappe.db.get_value("User", user, "user_type")
    print(f"User Type: {user_type}")
    
    intake_completed = frappe.db.get_value("User", user, "intake_completed")
    print(f"Intake Completed: {intake_completed}")

    # Re-implement logic here to verify expected outcome based on DB state
    if "Patient" in roles or user_type == "Website User":
        if intake_completed:
            route = "/patient_dashboard"
        else:
            route = "/glp1-intake-wizard"
        
        print(f"Calculated Route: {route}")
        if route == expected_route:
            print("✅ PASS: Route matches expected.")
        else:
            print(f"❌ FAIL: Expected {expected_route}, got {route}")
    else:
        print("User is not a patient.")

if __name__ == "__main__":
    frappe.init(site="koraflow-site", sites_path=sites_path)
    frappe.connect()
    
    # Test Patient0 (Assuming new user, so intake_completed should be 0/False/None)
    verify_redirect_logic("patient0@example.com", "/glp1-intake-wizard") # Update email if needed based on check_patient0.py output
    
    # Create a dummy user that IS completed to verify positive case?
    # Or just manually verify logic flow.
    
    # Let's perform a direct import test if possible
    try:
        from koraflow_core.utils.auth import on_login
        print("\n--- Testing Actual on_login Function ---")
        
        user_name = frappe.db.get_value("User", {"email": ["like", "%Patient0%"]}, "name")
        if user_name:
             # Reset response
            frappe.local.response = {}
            on_login(MockLoginManager(user_name))
            print(f"Resulting Response: {frappe.local.response}")
    except ImportError:
        print("Could not import auth module directly in this script context.")
