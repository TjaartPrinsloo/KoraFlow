import frappe

def execute():
    # THE FIX: Move the Tab Break to be AFTER the last field of the previous tab
    # Previous tab is 'Medical History', last field is 'other_risk_factors'
    # This prevents the new tab from "stealing" the fields of the Medical History tab.
    
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}, "insert_after", "other_risk_factors")
    
    # Also ensure 'section_key_biometrics' follows the tab (it should already, but being safe)
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "insert_after", "glp1_intake_tab")

    frappe.clear_cache(doctype="Patient")
