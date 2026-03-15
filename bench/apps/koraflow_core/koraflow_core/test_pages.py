import frappe
from frappe.desk.desktop import get_workspace_sidebar_items

def test_pages():
    frappe.set_user('nurse@koraflow.com')
    items = get_workspace_sidebar_items()
    pages = [p.get('name') for p in items.get('pages', [])]
    print(f"Pages for nurse: {pages}")
    
    u = frappe.get_user()
    u.build_permissions()
    print(f"Allowed modules for nurse: {u.allow_modules}")

if __name__ == "__main__":
    test_pages()
