import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # 1. CLEANUP: Delete existing Property Setters to start fresh
    fields = ["personal_and_social_history", "occupation", "column_break_25", "marital_status", "dashboard_tab", "address_and_contact_tab"]
    for f in fields:
        frappe.db.delete("Property Setter", {"doc_type": "Patient", "field_name": f, "property": "insert_after"})
        frappe.db.delete("Property Setter", {"doc_type": "Patient", "field_name": f, "property": "idx"})

    # 2. DEFINE CHAIN
    # patient_details (Standard)
    #   -> personal_and_social_history (Section)
    #       -> occupation (Col 1)
    #       -> column_break_25 (Col Break)
    #       -> marital_status (Col 2)
    #   -> dashboard_tab (Tab Break)
    
    # We will enforce this chain using insert_after
    
    # Move Section to follow patient_details
    make_property_setter("Patient", "personal_and_social_history", "insert_after", "patient_details", "Section Break")
    
    # Move first field to follow Section
    make_property_setter("Patient", "occupation", "insert_after", "personal_and_social_history", "Data")
    
    # Move Column Break to follow occupation
    make_property_setter("Patient", "column_break_25", "insert_after", "occupation", "Column Break")
    
    # Move marital_status to follow Column Break
    make_property_setter("Patient", "marital_status", "insert_after", "column_break_25", "Select")
    
    # CRITICAL: Move Dashboard Tab to follow the SECTION Header (or the last field?)
    # If we move it to follow the Section Header, Frappe might place the section fields *inside* the dashboard tab if we aren't careful?
    # No, Tab Break ends the previous tab.
    # If we put Dashboard Tab AFTER Personal History Section, then Personal History Section is in the PREVIOUS tab.
    # But where do the fields go?
    # If fields are inserted after Personal History, they are between Personal History and Dashboard Tab.
    # Which is exactly what we want.
    
    # Let's try anchoring Dashboard Tab to marital_status again? No, it failed.
    # Let's anchor it to 'personal_and_social_history' AND use a high global idx?
    # No, let's just anchor it to 'marital_status' BUT ALSO clear the cache very aggressively.
    # And maybe use `priority`? No such thing.
    
    # Alternative: Anchor Dashboard Tab to 'personal_and_social_history' but ensure 'occupation' insert_after is 'personal_and_social_history' too?
    # The sort is stable?
    
    # Let's try anchoring Dashboard Tab to 'marital_status' again properly after deletion.
    make_property_setter("Patient", "dashboard_tab", "insert_after", "marital_status", "Tab Break")

    frappe.clear_cache(doctype="Patient")
