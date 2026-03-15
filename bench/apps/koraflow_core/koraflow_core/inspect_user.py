import frappe
import json

def inspect_user():
    user = frappe.get_doc("User", "nurse@koraflow.com")
    print(f"User: {user.name}")
    print(f"Role Profile: {user.role_profile_name}")
    print(f"Roles: {[r.role for r in user.roles]}")
    
    if user.role_profile_name:
        profile = frappe.get_doc("Role Profile", user.role_profile_name)
        print(f"Profile Roles: {[r.role for r in profile.roles]}")

    # Check effective roles
    print(f"Effective Roles: {frappe.get_roles('nurse@koraflow.com')}")

if __name__ == "__main__":
    inspect_user()
