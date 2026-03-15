import frappe
from frappe.desk.desktop import get_workspace_sidebar_items

def check_sidebar():
    frappe.set_user("nurse@koraflow.com")
    items = get_workspace_sidebar_items()
    print("Workspaces visible to Nurse:")
    for item in items.get('pages', []):
        print(f" - {item.get('name')}")

if __name__ == "__main__":
    check_sidebar()
