import frappe

def test_workspaces():
    frappe.set_user("nurse@koraflow.com")
    from frappe.desk.desktop import get_workspace_sidebar_items
    
    # Check what frappe natively thinks
    items = get_workspace_sidebar_items()
    print("Vanilla frappe items:")
    for p in items.get('pages', []):
        print(f" - {p.get('name')}")
        
    print("\nAllowed Workspaces in apps.py (which uses our wrapper):")
    import koraflow_core.utils.workspace_filter as wf
    wrapped_items = wf.get_workspace_sidebar_items()
    for p in wrapped_items.get('pages', []):
        print(f" - {p.get('name')}")

if __name__ == "__main__":
    test_workspaces()
