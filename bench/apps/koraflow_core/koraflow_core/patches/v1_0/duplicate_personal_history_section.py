import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Strategy: 
    # 1. Hide immovable standard Section Break 'personal_and_social_history'.
    # 2. Create NEW Custom Section Break 'custom_personal_history' inserted after 'language' (in Details tab).
    # 3. Move standard fields 'occupation', 'column_break_field', 'marital_status' to follow new section.
    
    # 1. Hide Standard Section
    make_property_setter("Patient", "personal_and_social_history", "hidden", 1, "Section Break")
    
    # 2. Create Duplicate Section Header (Custom Field)
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_personal_history"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_personal_history",
            "label": "Personal and Social History",
            "fieldtype": "Section Break",
            "insert_after": "language", # Before 'More Information'
            "hidden": 0
        }).insert(ignore_permissions=True)
    else:
        # Ensure it is visible and in place
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "custom_personal_history"}, "insert_after", "language")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "custom_personal_history"}, "hidden", 0)

    # 3. Move Content Fields to new location
    # We use Property Setters for standard fields
    
    # Occupation -> follows new section
    make_property_setter("Patient", "occupation", "insert_after", "custom_personal_history", "Data")
    
    # Column Break -> follows occupation
    # Use existing column break? 'column_break_25'
    make_property_setter("Patient", "column_break_25", "insert_after", "occupation", "Column Break")
    
    # Marital Status -> follows Column Break
    make_property_setter("Patient", "marital_status", "insert_after", "column_break_25", "Select")

    # 4. Chain 'More Information' (standard) to follow 'marital_status'? 
    # To Ensure 'More Information' appears AFTER our inserted section.
    make_property_setter("Patient", "more_info", "insert_after", "marital_status", "Section Break")
    
    frappe.clear_cache(doctype="Patient")
