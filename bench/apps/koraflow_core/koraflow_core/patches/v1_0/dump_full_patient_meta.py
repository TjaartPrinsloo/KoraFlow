import frappe

def execute():
    meta = frappe.get_meta("Patient")
    print("FULL PATIENT FIELD ORDER:")
    for i, f in enumerate(meta.fields):
        # Print index, label, fieldname, and hidden status
        # Highlight our interesting fields
        mark = ""
        if f.fieldname in ["glp1_intake_tab", "section_key_biometrics", "blood_group", "intake_height_cm", "glp1_intake_forms"]:
            mark = " <--- CHECK HERE"
        
        hidden = "[HIDDEN]" if f.hidden else "[VISIBLE]"
        print(f"{i}: [{f.fieldtype}] {f.label} ({f.fieldname}) {hidden} {mark}")
