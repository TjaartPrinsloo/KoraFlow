
import frappe

def check_context():
    email = "test_patient@example.com"
    print(f"Checking for email: {email}")
    
    # Check User
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        print(f"User found: {user.name}, Type: {user.user_type}, Roles: {[r.role for r in user.roles]}")
    else:
        print("User NOT found")

    # Check Patient direct (admin)
    patient = frappe.db.get_value("Patient", {"email": email}, "name")
    print(f"Patient (Admin Check): {patient}")

    # Check Permissions
    # Simulating what happens in the controller? No, just checking perm config
    roles = frappe.get_roles(email)
    print(f"Roles for {email}: {roles}")
    
    # Check DocPerm
    perms = frappe.get_all("Custom DocPerm", filters={"parent": "Patient", "role": "Patient"}, fields=["read", "write", "create"])
    if not perms:
        perms = frappe.get_all("DocPerm", filters={"parent": "Patient", "role": "Patient"}, fields=["read", "write", "create"])
    print(f"Permissions for 'Patient' role on 'Patient' DocType: {perms}")

check_context()
