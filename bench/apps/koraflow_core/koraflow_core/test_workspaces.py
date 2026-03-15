import frappe
from frappe.desk.desktop import get_workspace_sidebar_items
import json

def test_workspaces():
    frappe.set_user('nurse@koraflow.com')
    sidebar = get_workspace_sidebar_items()
    print("SIDEBAR FOR NURSE:")
    print(json.dumps(sidebar, indent=2))

if __name__ == "__main__":
    test_workspaces()
