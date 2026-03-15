
import frappe
from frappe.utils.password import update_password

def setup_ui_test_data():
    print("Setting up UI Test Data (Bypass Mode)...")

    agent_email = "test.sales.agent@koraflow.com"
    patient_email = "test.patient.ui@koraflow.com"
    
    # 1. Setup Sales Agent
    if frappe.db.exists("User", agent_email):
        print(f"User {agent_email} exists. Updating password directly.")
        update_password(agent_email, "Test@123456")
        frappe.db.set_value("User", agent_email, "user_type", "System User")
        user = frappe.get_doc("User", agent_email)
        user.add_roles("Sales Agent", "System Manager")
        print("✅ Sales Agent Setup Complete.")
    
    # 2. Setup Patient User
    if not frappe.db.exists("User", patient_email):
        print(f"Creating Patient User {patient_email}...")
        user = frappe.new_doc("User")
        user.email = patient_email
        user.first_name = "Test"
        user.last_name = "Patient"
        user.user_type = "Website User"
        user.flags.ignore_permissions = True
        user.insert()
        print("✅ Patient User Created.")
    
    user_doc = frappe.get_doc("User", patient_email)
    user_doc.add_roles("Patient")
    update_password(patient_email, "Test@123456")
    print(f"✅ User setup for {patient_email} complete.")

    # 3. Setup Patient Record (Required for Dashboard)
    patient_name = frappe.db.get_value("Patient", {"email": patient_email}, "name")
    if not patient_name:
        print("Creating Patient record...")
        patient = frappe.new_doc("Patient")
        patient.first_name = "Test"
        patient.last_name = "Patient"
        patient.email = patient_email
        patient.sex = "Male"
        patient.status = "Active"
        patient.invite_user = 0 # Don't trigger user creation hook
        patient.user_id = patient_email # Link manually
        patient.flags.ignore_permissions = True
        patient.insert()
        patient_name = patient.name
        print(f"✅ Patient Record Created: {patient_name}")
    else:
        print(f"Patient record {patient_name} already exists. Linking to user...")
        frappe.db.set_value("Patient", patient_name, "user_id", patient_email)
        print("✅ Linked existing patient record to user.")

    # Fix Role Permission for Sales Agent Desk Access
    try:
        role = frappe.get_doc("Role", "Sales Agent")
        role.desk_access = 1
        role.save()
        print("✅ Verified Desk Access for Sales Agent Role")
    except:
        pass

    frappe.db.commit()
    print("Done.")
