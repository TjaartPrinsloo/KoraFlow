import frappe

def test_nurse_patient_access():
    target_user = "nurse@koraflow.com"
    # Set the user context correctly
    frappe.set_user(target_user)
    
    # Check roles
    roles = frappe.get_roles()
    print(f"Testing access for User: {target_user}")
    print(f"Roles: {roles}")
    
    # Try fetching patients
    try:
        patients = frappe.get_list("Patient", fields=["name", "first_name", "last_name"])
        print(f"Successfully fetched {len(patients)} patients.")
        if patients:
            print("First few patients found:")
            for p in patients[:3]:
                print(f" - {p.name}: {p.first_name} {p.last_name}")
        else:
            print("No patients returned. Check permission query logic.")
    except Exception as e:
        print(f"Error fetching patients: {e}")

if __name__ == "__main__":
    test_nurse_patient_access()
