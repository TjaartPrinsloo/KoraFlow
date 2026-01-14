import frappe

def execute():
    # 1. Create a Key Biometrics Section Break in Details Tab (after user_id)
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "section_key_biometrics",
            "label": "Key Biometrics",
            "fieldtype": "Section Break",
            "insert_after": "user_id",
            "hidden": 0,
            "collapsible": 0
        }).insert(ignore_permissions=True)
    else:
        # Ensure it's visible and correctly placed
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "insert_after", "user_id")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "hidden", 0)

    # 2. List of fields to move and unhide
    biometric_fields = [
        "intake_height_cm", 
        "intake_weight_kg", 
        "bmi", 
        "bmi_category", 
        "goal_weight",
        "weight_to_lose"
    ]

    # 3. Move them sequentially after the new section
    previous_field = "section_key_biometrics"
    for fieldname in biometric_fields:
        if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": fieldname}):
            # Update Custom Field definition
            frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": fieldname}, "insert_after", previous_field)
            frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": fieldname}, "hidden", 0)
            
            # Remove any Property Setter causing it to be hidden (from previous patch)
            frappe.db.delete("Property Setter", {"doc_type": "Patient", "field_name": fieldname, "property": "hidden"})
            
            previous_field = fieldname
    
    frappe.clear_cache(doctype="Patient")
