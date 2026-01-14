import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Strategy: Insert 'Personal and Social History' section BEFORE 'More Information' section.
    # Target anchor: 'language' (last field of Customer Details section).
    
    # 1. CLEANUP specific fields first
    target_fields = ["personal_and_social_history", "occupation", "column_break_25", "marital_status", "dashboard_tab"]
    for f in target_fields:
         frappe.db.delete("Property Setter", {"doc_type": "Patient", "field_name": f})

    # 2. DO THE MOVE
    
    # Anchor Section Header to 'language'
    make_property_setter("Patient", "personal_and_social_history", "insert_after", "language", "Section Break")
    
    # Anchor fields to follow (standard chain)
    make_property_setter("Patient", "occupation", "insert_after", "personal_and_social_history", "Data")
    make_property_setter("Patient", "column_break_25", "insert_after", "occupation", "Column Break")
    make_property_setter("Patient", "marital_status", "insert_after", "column_break_25", "Select")

    # 3. Ensure 'more_info' follows 'marital_status'??
    # 'more_info' is a standard field with standard location.
    # If we insert 'marital_status' after 'column_break_25'...
    # The sort mechanism will effectively place 'personal_and_social_history' group after 'language'.
    # And 'more_info' (which naturally follows 'language') will now follow our new group?
    # Yes, because 'more_info' follows 'language' by default idx.
    # We are injecting items with 'insert_after'='language'.
    # So both 'more_info' and 'personal_and_social_history' want to be after 'language'.
    # Which one wins? The one with explicitly set 'insert_after' usually wins against implicit.
    # Or we can chain 'more_info' to 'marital_status' to be sure.
    
    make_property_setter("Patient", "more_info", "insert_after", "marital_status", "Section Break")

    frappe.clear_cache(doctype="Patient")
