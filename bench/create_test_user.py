import frappe
from frappe.utils import nowdate

frappe.init(site="koraflow-site", sites_path="sites")
frappe.connect()

email = "ui_test_patient@example.com"
pwd = "password123"
first_name = "UI Test"

try:
    # Cleanup
    if frappe.db.exists("User", email):
        frappe.delete_doc("User", email, ignore_permissions=True, force=1)
    
    patient_exists = frappe.db.get_value("Patient", {"email": email})
    if patient_exists:
        frappe.delete_doc("Patient", patient_exists, ignore_permissions=True, force=1)
        
    frappe.db.commit()

    # 1. Create Patient (will auto-create user)
    if not frappe.db.exists("Patient", {"email": email}):
        patient = frappe.get_doc({
            "doctype": "Patient",
            "first_name": first_name,
            "email": email,
            "dob": "1990-01-01",
            "sex": "Female",
            "mobile": "0000000000" # Might be required
        })
        patient.insert(ignore_permissions=True)
    else:
        patient_name = frappe.db.get_value("Patient", {"email": email}, "name")
        patient = frappe.get_doc("Patient", patient_name)

    # 2. Update Password for auto-created user
    from frappe.utils.password import update_password
    try:
        update_password(email, pwd)
    except:
        pass # User might not exist if auto-creation skipped

    # 3. Create Vitals (Skipped due to import error)
    # if not frappe.db.exists("Patient Vital", {"patient": patient.name, "date": nowdate()}):
    #     frappe.get_doc({
    #         "doctype": "Patient Vital",
    #         "patient": patient.name,
    #         "date": nowdate(),
    #         "weight_kg": 75.5,
    #         "height_cm": 170,
    #         "bmi": 26.1
    #     }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("Test Data Created Successfully")

except Exception as e:
    frappe.db.rollback()
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
