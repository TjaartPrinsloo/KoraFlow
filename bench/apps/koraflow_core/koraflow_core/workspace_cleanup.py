import frappe

def cleanup_nurse_workspaces():
    # 1. Delete redundant workspaces
    workspaces_to_delete = ["Nurse Workcenter", "Nurse Dashboard"]
    for ws_name in workspaces_to_delete:
        if frappe.db.exists("Workspace", ws_name):
            frappe.delete_doc("Workspace", ws_name, ignore_permissions=True, force=True)
            print(f"Deleted workspace: {ws_name}")

    # 2. Set Healthcare as default for the nurse
    user_email = "nurse@koraflow.com"
    if frappe.db.exists("User", user_email):
        frappe.db.set_value("User", user_email, "default_workspace", "Healthcare")
        print(f"Set Healthcare as default workspace for {user_email}")

    frappe.db.commit()
    frappe.clear_cache()
    print("Cleanup complete and cache cleared.")

if __name__ == "__main__":
    cleanup_nurse_workspaces()
