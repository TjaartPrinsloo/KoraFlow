import frappe

def set_custom_logo():
    """Set the S2W custom logo in Navbar Settings and System Settings."""
    s2w_logo = "/assets/koraflow_core/images/s2w_logo.png"
    s2w_favicon = "/assets/koraflow_core/images/s2w_logo.png"

    # --- 1. Navbar Settings: app_logo ---
    navbar = frappe.get_single("Navbar Settings")
    navbar.app_logo = s2w_logo
    navbar.save()
    print(f"Navbar Settings: app_logo set to {s2w_logo}")

    # --- 2. System Settings: favicon ---
    ss = frappe.get_single("System Settings")
    ss.favicon = s2w_favicon
    ss.save()
    print(f"System Settings: favicon set to {s2w_favicon}")

    frappe.db.commit()
    frappe.clear_cache()
    print("Done. S2W branding applied.")
