import frappe
from frappe import _
import os

# Explicitly set path to sites
sites_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/sites"

def check_user():
    search_term = "Patient0"
    user_id = frappe.db.get_value("User", {"email": ["like", f"%{search_term}%"]}, "name")
    
    if not user_id:
        print(f"User matching {search_term} does NOT exist.")
        return

    user = frappe.get_doc("User", user_id)
    print(f"Found User: {user.name}")
    print(f"Email: {user.email}")
    print(f"User Type: {user.user_type}")
    print(f"Roles: {user.get_roles()}")
    print(f"Enabled: {user.enabled}")
    
    # Check if Patient record exists
    patient = frappe.db.get_value("Patient", {"user_id": user.name}, "name")
    if patient:
        print(f"Linked User to Patient: {patient}")
    else:
        # Check by email
        patient_by_email = frappe.db.get_value("Patient", {"email": user.email}, "name")
        print(f"Linked Patient by Email: {patient_by_email}")

if __name__ == "__main__":
    frappe.init(site="koraflow-site", sites_path=sites_path)
    frappe.connect()
    check_user()
