import frappe

def clear_user_cache():
    frappe.clear_cache(user='nurse@koraflow.com')
    # Manually delete document cache
    frappe.cache.delete_key(f"document_cache::User::nurse@koraflow.com")
    
    doc = frappe.get_doc("User", "nurse@koraflow.com")
    print(len(doc.get("block_modules")))
    print("Healthcare in block_modules?", "Healthcare" in [m.module for m in doc.get("block_modules")])

if __name__ == "__main__":
    clear_user_cache()
