import frappe
from frappe.desk.desktop import Workspace

def debug_workspace_class():
    frappe.set_user('nurse@koraflow.com')
    page_dict = frappe.get_doc("Workspace", "Nurse View").as_dict()
    print("Page Dict:", page_dict.get("name"), page_dict.get("public"), page_dict.get("is_hidden"))
    
    try:
        ws = Workspace(page_dict, True)
        print("Workspace init successful")
        print("ws.is_permitted():", ws.is_permitted())
        
        # Manually trace is_permitted
        allowed = [d.role for d in ws.doc.roles]
        print(f"Allowed roles for workspace: {allowed}")
        roles = frappe.get_roles()
        print(f"User roles: {roles}")
        
        from frappe.utils import has_common
        print("has_common?", has_common(roles, allowed))
        
    except Exception as e:
        print(f"Error initializing Workspace: {e}")

if __name__ == "__main__":
    debug_workspace_class()
