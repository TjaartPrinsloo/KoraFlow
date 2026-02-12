
import frappe

def check_user():
    user = frappe.get_doc("User", "test_patient@example.com")
    print(f"User Type: {user.user_type}")
    print(f"Roles: {[r.role for r in user.roles]}")

check_user()
