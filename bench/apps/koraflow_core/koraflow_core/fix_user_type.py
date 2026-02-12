
import frappe

def fix_user():
    frappe.db.commit()
    user = frappe.get_doc("User", "test_patient@example.com")
    user.user_type = "Website User"
    user.add_roles("Patient")
    user.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Updated User Type: {user.user_type}")
    print(f"Updated Roles: {[r.role for r in user.roles]}")

fix_user()
