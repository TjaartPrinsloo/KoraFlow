import frappe
import json

def inspect_nurse_view():
    try:
        doc = frappe.get_doc("Workspace", "Nurse View")
        print(f"Workspace: {doc.name}")
        print(f"Roles: {[r.role for r in doc.roles]}")
        print(f"Module: {doc.module}")
        print(f"Public: {doc.public}")
        print(f"Is Hidden: {doc.is_hidden}")
    except frappe.DoesNotExistError:
        print("Nurse View Workspace does not exist!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_nurse_view()
