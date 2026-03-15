import frappe
from frappe.desk.desktop import get_workspace_sidebar_items

def trace_workspace():
    frappe.set_user('nurse@koraflow.com')
    workspaces = frappe.get_all(
        "Workspace",
        fields=["name", "module", "public", "for_user"],
        filters={"is_hidden": 0}
    )
    
    nurse_ws = [w for w in workspaces if w.name == "Nurse View"]
    print(f"Nurse View in DB: {nurse_ws}")
    
    if nurse_ws:
        ws_doc = frappe.get_doc("Workspace", "Nurse View")
        roles = [r.role for r in ws_doc.roles]
        print(f"Roles for Nurse View: {roles}")
        
    user = frappe.get_doc("User", frappe.session.user)
    print(f"Roles for User: {frappe.get_roles()}")
    print(f"Blocked modules for user: {user.get_blocked_modules()}")
    
    # Simulate Frappe's filtering
    from frappe.desk.desktop import has_access
    print(f"has_access('Nurse View'): {has_access(ws_doc)}")

if __name__ == "__main__":
    trace_workspace()
