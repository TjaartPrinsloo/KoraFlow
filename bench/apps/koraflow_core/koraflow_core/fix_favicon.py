import frappe

def fix_favicon():
    ws = frappe.get_single("Website Settings")
    ws.favicon = "/assets/koraflow_core/images/s2w_logo.png"
    ws.save()
    frappe.db.commit()
    frappe.clear_cache()
    print(f"Website Settings: favicon set to {ws.favicon}")
