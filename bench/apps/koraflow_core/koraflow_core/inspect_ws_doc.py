import frappe
import json

def inspect_workspace():
    doc = frappe.get_doc("Workspace", "Nurse View")
    print(f"Workspace: {doc.name}")
    print(f"Public: {doc.public}")
    print(f"Is Hidden: {doc.is_hidden}")
    print(f"Roles: {json.dumps([d.as_dict() for d in doc.get('roles')], indent=2) if doc.get('roles') else '[]'}")
    
    # Check if there are any other restriction fields
    print(f"Restrict to Domain: {doc.restrict_to_domain}")
    
    # Check if the Nurse role actually exists
    print(f"Nurse Role Exists: {frappe.db.exists('Role', 'Nurse')}")
    
    # Check Nurse user roles
    frappe.set_user("nurse@koraflow.com")
    print(f"Current User Roles: {frappe.get_roles()}")

if __name__ == "__main__":
    inspect_workspace()
