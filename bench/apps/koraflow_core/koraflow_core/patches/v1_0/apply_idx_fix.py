import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Attempt to use IDX to force order, as insert_after is failing specifically for standard field move
    
    # 1. Get IDX of the tab insertion point (other_risk_factors)
    # This is hard because it's a standard field, but let's assume a high numbering start
    start_idx = 200
    
    # Set GLP-1 Tab
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}, "idx", start_idx)
    
    # Set Key Biometrics Section
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "idx", start_idx + 1)
    
    # Set Blood Group (via Property Setter)
    make_property_setter("Patient", "blood_group", "idx", start_idx + 2, "Int")
    
    # Set Height
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "intake_height_cm"}, "idx", start_idx + 3)
    
    frappe.clear_cache(doctype="Patient")
