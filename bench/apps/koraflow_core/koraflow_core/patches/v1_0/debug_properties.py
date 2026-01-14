import frappe

def execute():
    # Check Property Setter
    ps_val = frappe.db.get_value("Property Setter", 
        {"doc_type": "Patient", "field_name": "blood_group", "property": "insert_after"}, 
        "value")
    print(f"Property Setter (blood_group insert_after): {ps_val}")

    # Check Custom Field
    cf = frappe.db.get_value("Custom Field", 
        {"dt": "Patient", "fieldname": "section_key_biometrics"}, 
        ["name", "insert_after"], as_dict=True)
    print(f"Custom Field (section_key_biometrics): {cf}")
