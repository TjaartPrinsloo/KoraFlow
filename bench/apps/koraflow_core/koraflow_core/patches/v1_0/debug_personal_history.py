import frappe

def execute():
    # Check Property Setter for section and fields
    fields = ["personal_and_social_history", "occupation", "marital_status"]
    
    print("DEBUG PERSONAL HISTORY PROPERTIES:")
    for fn in fields:
        ps_insert = frappe.db.get_value("Property Setter", 
            {"doc_type": "Patient", "field_name": fn, "property": "insert_after"}, 
            "value")
        print(f"Field: {fn} -> insert_after Property Setter: {ps_insert}")
        
        # Check actual field object just in case
        f_meta = frappe.get_meta("Patient").get_field(fn)
        if f_meta:
             print(f"Field: {fn} -> Actual Metadata insert_after: {getattr(f_meta, 'insert_after', 'None')}")
