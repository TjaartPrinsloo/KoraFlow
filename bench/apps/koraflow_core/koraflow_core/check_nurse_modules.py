import frappe

def check_nurse_allowed_modules():
    frappe.set_user("nurse@koraflow.com")
    user = frappe.get_user()
    print(f"User: {user.name}")
    print(f"Roles: {user.get_roles()}")
    
    # Force rebuild permissions to be sure
    user.build_permissions()
    print(f"Calculated Allowed Modules: {user.allow_modules}")
    
    # Check if 'Healthcare' is in it
    print(f"Is 'Healthcare' allowed? {'Healthcare' in user.allow_modules}")
    
    # Check if 'Patient' is in can_read
    print(f"Can read Patient? {'Patient' in user.can_read}")
    
    # Check 'Patient' DocType module
    print(f"Patient Module: {frappe.get_meta('Patient').module}")

if __name__ == "__main__":
    check_nurse_allowed_modules()
