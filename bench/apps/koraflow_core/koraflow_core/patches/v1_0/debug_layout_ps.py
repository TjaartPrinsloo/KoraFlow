import frappe

def execute():
    # Check Property Setter for section and fields
    fields = ["personal_and_social_history", "dashboard_tab"]
    
    print("DEBUG LAYOUT PROPERTIES:")
    for fn in fields:
        ps_insert = frappe.db.get_value("Property Setter", 
            {"doc_type": "Patient", "field_name": fn, "property": "insert_after"}, 
            "value")
        print(f"Field: {fn} -> insert_after Property Setter: {ps_insert}")
        
        ps_idx = frappe.db.get_value("Property Setter", 
            {"doc_type": "Patient", "field_name": fn, "property": "idx"}, 
            "value")
        if ps_idx:
             print(f"Field: {fn} -> idx Property Setter: {ps_idx}")
