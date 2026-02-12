
import frappe
from frappe.permissions import add_permission, update_permission_property

def fix_access():
    frappe.db.commit()
    
    # 1. Fix Permissions
    # Ensure Patient role has Read access to critical DocTypes
    doctypes = ["Patient", "Patient Vital", "GLP-1 Patient Prescription", "GLP-1 Shipment", "Quotation", "Sales Invoice"]
    role = "Patient"
    
    for dt in doctypes:
        # Check if permission exists
        if not frappe.db.exists("DocPerm", {"parent": dt, "role": role}):
            print(f"Adding permission for {dt}...")
            add_permission(dt, role, 0) # level 0
            update_permission_property(dt, role, 0, "read", 1)
            update_permission_property(dt, role, 0, "write", 1) # Allow write for Vitals? Maybe specific.
            update_permission_property(dt, role, 0, "create", 1)
        else:
            print(f"Updating permission for {dt}...")
            update_permission_property(dt, role, 0, "read", 1)
            # Ensure write for Vital
            if dt == "Patient Vital":
                update_permission_property(dt, role, 0, "write", 1)
                update_permission_property(dt, role, 0, "create", 1)
                
    # 2. Fix Data
    email = "test_patient@example.com"
    patient_name = frappe.db.get_value("Patient", {"email": email}, "name")
    
    if not patient_name:
        # Check if any patient exists with this name but wrong email
        p = frappe.db.get_value("Patient", {"first_name": "Test", "last_name": "Patient"}, "name")
        if p:
            print(f"Found orphaned patient {p}. Updating email...")
            frappe.db.set_value("Patient", p, "email", email)
            frappe.db.set_value("Patient", p, "status", "Active")
        else:
            print("Creating new Patient record...")
            p_doc = frappe.new_doc("Patient")
            p_doc.first_name = "Test"
            p_doc.last_name = "Patient"
            p_doc.email = email
            p_doc.sex = "Female"
            p_doc.dob = "1990-01-01"
            p_doc.status = "Active"
            p_doc.save(ignore_permissions=True)
            print(f"Created Patient: {p_doc.name}")
    else:
        print(f"Patient record exists: {patient_name}")
        
    frappe.db.commit()
    print("Access Fix Complete.")

fix_access()
