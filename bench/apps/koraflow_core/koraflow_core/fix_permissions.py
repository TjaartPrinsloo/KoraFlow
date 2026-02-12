import frappe

def run():
    print("Fixing permissions...")
    try:
        user = frappe.get_doc("User", "Administrator")
        user.add_roles("Patient")
        print("Role 'Patient' added to Administrator.")
    except Exception as e:
        print(f"Error adding role: {e}")

    try:
        from frappe.utils.password import update_password
        update_password("test.patient.new.456@example.com", "admin")
        print("Password updated for test user.")
    except Exception as e:
        print(f"Error updating password: {e}")
    
    frappe.db.commit()
    print("Success.")
