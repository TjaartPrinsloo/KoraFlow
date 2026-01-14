import frappe

def execute():
    fields = ["personal_and_social_history", "dashboard_tab"]
    
    print("DEBUG IDX PROPERTIES:")
    for fn in fields:
        ps_idx = frappe.db.get_value("Property Setter", 
            {"doc_type": "Patient", "field_name": fn, "property": "idx"}, 
            "value")
        print(f"Field: {fn} -> idx Property Setter: {ps_idx}")
