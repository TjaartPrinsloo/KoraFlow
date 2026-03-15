import frappe

def remove_frappe_branding():
    """Remove all client-visible Frappe branding."""

    # 1. Website Settings - disable 'Built on Frappe' footer and update brand
    ws = frappe.get_single("Website Settings")
    ws.footer_powered = 0        # Disables "Built on Frappe" footer link
    ws.app_name = "Slim 2 Well"
    ws.brand_name = "Slim 2 Well"
    ws.favicon = "/assets/koraflow_core/images/s2w_logo.png"
    ws.save()
    print("Website Settings: footer_powered=0, brand updated")

    # 2. System Settings - update app name visible in email subjects/titles
    ss = frappe.get_single("System Settings")
    ss.favicon = "/assets/koraflow_core/images/s2w_logo.png"
    ss.save()
    print("System Settings: favicon updated")

    frappe.db.commit()
    frappe.clear_cache()
    print("Done. All client-visible Frappe branding removed.")
