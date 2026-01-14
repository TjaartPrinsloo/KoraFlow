import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Fetch standard field idx as baseline
    meta = frappe.get_meta("Patient")
    
    # Defaults in case not found, though they are standard
    base_idx = 100 
    for f in meta.fields:
        if f.fieldname == "patient_details":
            base_idx = f.idx
            break
            
    print(f"Base IDX for patient_details: {base_idx}")
    
    # We want Personal History to start right after
    start_idx = base_idx + 1
    
    # 1. Personal History Section Header
    make_property_setter("Patient", "personal_and_social_history", "idx", start_idx, "Int")
    
    # 2. Fields inside it (approximate spacing)
    make_property_setter("Patient", "occupation", "idx", start_idx + 1, "Int")
    make_property_setter("Patient", "column_break_25", "idx", start_idx + 2, "Int")
    make_property_setter("Patient", "marital_status", "idx", start_idx + 3, "Int")
    
    # 3. Push Dashboard Tab down
    make_property_setter("Patient", "dashboard_tab", "idx", start_idx + 10, "Int")

    # 4. Also ensure 'Address & Contact' (which follows Dashboard) is pushed if needed
    # Usually relative idx is enough, but let's be safe if it has a low standard idx
    # address_and_contact_tab
    make_property_setter("Patient", "address_and_contact_tab", "idx", start_idx + 20, "Int")

    frappe.clear_cache(doctype="Patient")
