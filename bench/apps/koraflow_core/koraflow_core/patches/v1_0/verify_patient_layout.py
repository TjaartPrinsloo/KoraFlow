import frappe

def execute():
    # Load the full metadata for Patient, which includes standard fields + custom fields + property setters
    meta = frappe.get_meta("Patient")
    
    print("COMPUTED LAYOUT FOR 'GLP-1 Intake' TAB:")
    
    in_glp1_tab = False
    for field in meta.fields:
        # Detect start of our tab
        if field.fieldname == "glp1_intake_tab":
            in_glp1_tab = True
            print(f"--- START TAB: {field.label} ({field.fieldname}) ---")
            continue
            
        # Detect start of next tab (end of our tab)
        if in_glp1_tab and field.fieldtype == "Tab Break":
            print(f"--- END TAB (Next: {field.label}) ---")
            in_glp1_tab = False
            break # No need to look further
            
        # Print fields inside our tab
        if in_glp1_tab:
            hidden_status = "(Hidden)" if field.hidden else "(Visible)"
            print(f" - [{field.fieldtype}] {field.label} ({field.fieldname}) {hidden_status}")

