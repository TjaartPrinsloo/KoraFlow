import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Move 'personal_and_social_history' section to the end of the 'Details' tab
    # The last field of Details tab is usually 'patient_details' or 'more_info' section.
    
    # We use Property Setter because this might be a standard field
    # (checked dump: it is standard [Section Break] Personal and Social History)
    
    target_field = "patient_details"
    
    # Ensure patient_details is visible so we can attach to it? It is visible.
    
    make_property_setter("Patient", "personal_and_social_history", "insert_after", target_field, "Section Break")
    
    # We also need to move the fields INSIDE this section if they are not automatically carried over?
    # Usually moving the Section Break is enough if the next field is a Break.
    # The next field after Personal History was 'occupation', 'column_break', 'marital_status'.
    # Then 'allergy_medical_and_surgical_history' (Section Break).
    # So moving 'personal_and_social_history' *should* mistakenly ONLY move the break if we are not careful,
    # OR it effectively moves the "start" of the section. 
    # In Frappe, fields belong to the section preceding them.
    # So if I move the Section Break 'personal_and_social_history' to after 'patient_details',
    # then 'occupation' (which follows it in standard order) *might* stay where it was if I don't move it too?
    # NO, standard fields order is defined by the 'fields' list index.
    # Property Setter 'insert_after' changes the display order.
    # If I only move the Section Header, the fields `occupation` etc. might appear under the PREVIOUS section (Medical History Tab) 
    # instead of the new location.
    
    # To be safe, I should move the fields too.
    fields_to_move = ["occupation", "column_break_25", "marital_status"]
    previous = "personal_and_social_history"
    
    for field in fields_to_move:
        make_property_setter("Patient", field, "insert_after", previous, frappe.get_meta("Patient").get_field(field).fieldtype)
        previous = field

    frappe.clear_cache(doctype="Patient")
