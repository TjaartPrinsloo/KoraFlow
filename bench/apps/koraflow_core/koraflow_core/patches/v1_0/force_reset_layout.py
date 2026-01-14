import frappe

def execute():
    # Delete conflicting Property Setters that might be hiding/moving things
    # especially for standard fields like blood_group
    frappe.db.delete("Property Setter", {
        "doc_type": "Patient", 
        "field_name": "blood_group"
    })
    
     # Delete any user-specific customization for the User
    frappe.db.delete("User Form Customization", {
        "doctype": "Patient"
    })

    # Re-apply our layout logic strictly
    # Ensure Blood Group is moved to the right spot via Property Setter (re-create it)
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    
    # Force Blood Group to be after section_key_biometrics
    make_property_setter("Patient", "blood_group", "insert_after", "section_key_biometrics", "Data")
    make_property_setter("Patient", "blood_group", "hidden", 0, "Check") # Ensure visible
    
    frappe.clear_cache(doctype="Patient")
