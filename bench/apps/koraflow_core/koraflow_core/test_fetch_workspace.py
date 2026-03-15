import frappe

def test_fetch_workspace():
    frappe.set_user('nurse@koraflow.com')
    try:
        doc = frappe.get_doc("Workspace", "Nurse View")
        print("Success fetching Nurse View")
    except Exception as e:
        print(f"Error fetching Nurse View: {e}")

    try:
        doc = frappe.get_doc("Workspace", "Welcome Workspace")
        print("Success fetching Welcome Workspace")
    except Exception as e:
        print(f"Error fetching Welcome Workspace: {e}")

if __name__ == "__main__":
    test_fetch_workspace()
