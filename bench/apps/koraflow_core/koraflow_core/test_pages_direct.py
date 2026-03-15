import frappe

def test_pages():
    frappe.set_user('nurse@koraflow.com')
    
    blocked_modules = frappe.get_cached_doc("User", frappe.session.user).get_blocked_modules()
    blocked_modules.append("Dummy Module")

    allowed_domains = [None, *frappe.get_active_domains()]

    filters = {
        "restrict_to_domain": ["in", allowed_domains],
        "module": ["not in", blocked_modules],
    }

    fields = [
        "name", "title", "for_user", "parent_page", "content", "public", "module", "icon", "indicator_color", "is_hidden"
    ]
    
    all_pages = frappe.get_all(
        "Workspace", fields=fields, filters=filters, order_by="sequence_id asc", ignore_permissions=True
    )
    
    print(f"Blocked Modules: {blocked_modules}")
    print(f"All Pages found: {[p.name for p in all_pages]}")

if __name__ == "__main__":
    test_pages()
