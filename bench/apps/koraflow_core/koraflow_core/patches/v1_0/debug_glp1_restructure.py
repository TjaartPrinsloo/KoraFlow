import frappe

def execute():
    # Fields to check
    fieldnames = [
        "glp1_intake_tab",
        "section_key_biometrics",
        "blood_group",
        "intake_height_cm",
        "intake_weight_kg",
        "bmi",
        "section_glp1_forms_visible",
        "glp1_intake_forms",
        "ai_medical_summary",
        "section_glp1_vitals"
    ]
    
    print("DEBUG RESTRUCTURE CHECK:")
    for fn in fieldnames:
        # Check Custom Fields
        cf = frappe.db.get_value("Custom Field", {"dt": "Patient", "fieldname": fn}, ["name", "insert_after", "hidden", "label"], as_dict=True)
        if cf:
            print(f"Custom Field: {fn} -> Insert After: {cf.insert_after}, Hidden: {cf.hidden}")
            continue
            
        # Check Standard Fields (like blood_group)
        # Note: Standard fields might have Property Setters modifying them
        ps_insert = frappe.db.get_value("Property Setter", {"doc_type": "Patient", "field_name": fn, "property": "insert_after"}, "value")
        ps_hidden = frappe.db.get_value("Property Setter", {"doc_type": "Patient", "field_name": fn, "property": "hidden"}, "value")
        
        if ps_insert or ps_hidden:
            print(f"Property Setter: {fn} -> Insert After: {ps_insert}, Hidden: {ps_hidden}")
        else:
             print(f"Standard/Missing: {fn} (No Custom Field or Property Setter found)")

    # Also check if 'section_key_biometrics' actually exists
    exists = frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"})
    print(f"Does section_key_biometrics exist? {exists}")
