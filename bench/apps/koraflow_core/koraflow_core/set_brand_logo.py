import frappe

def set_brand_logo():
    """Set brand_logo in Website Settings so emails use S2W logo, not Frappe's."""
    ws = frappe.get_single("Website Settings")
    # brand_logo is used in the standard email template header
    ws.brand_logo = "/assets/koraflow_core/images/s2w_logo.png"
    ws.footer_powered = 0  # Remove "Built on Frappe" footer
    ws.save()
    frappe.db.commit()
    frappe.clear_cache()
    print(f"Website Settings: brand_logo={ws.brand_logo}, footer_powered=0")
