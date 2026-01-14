import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # 1. DELETE Layout-affecting Property Setters for Patient
    # This clears "Customize Form" overrides for field positions/visibility
    ps_filters = {
        "doc_type": "Patient",
        "property": ["in", ["insert_after", "hidden", "idx"]]
    }
    frappe.db.delete("Property Setter", ps_filters)
    
    # 2. RE-APPLY our specific necessary overrides
    
    # Move standard field 'Blood Group' to our new section
    # We must re-apply this because we just deleted it above
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}):
        make_property_setter("Patient", "blood_group", "insert_after", "section_key_biometrics", "Data")
        make_property_setter("Patient", "blood_group", "hidden", 0, "Check")

    # 3. Ensure 'Custom Fields' themselves have correct insert_after
    # (Sometimes Custom Fields get messed up if they referred to property-setter-moved fields)
    
    # Key Biometrics -> After GLP-1 Tab
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "insert_after", "glp1_intake_tab")
    
    # Height -> After Blood Group
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "intake_height_cm"}, "insert_after", "blood_group")

    # Forms Section -> After visible biometrics (weight_to_lose)
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_forms_visible"}, "insert_after", "weight_to_lose")
    
    frappe.clear_cache(doctype="Patient")
