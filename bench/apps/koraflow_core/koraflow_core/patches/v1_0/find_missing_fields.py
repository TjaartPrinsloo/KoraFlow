import frappe

def execute():
    # Search for likely missing fields
    fields = frappe.db.get_all("Custom Field", 
        filters={"dt": "Patient"}, 
        fields=["name", "fieldname", "label", "fieldtype", "insert_after", "hidden"],
    )
    
    print("MATCHING FIELDS:")
    found = False
    for f in fields:
        # Check for keywords related to the missing components
        if any(x in str(f.values()).lower() for x in ["table", "summary", "intake form", "form", "glp"]):
            print(f)
            found = True
            
    if not found:
        print("No matching custom fields found. Checking standard DocType fields...")
        patient_meta = frappe.get_meta("Patient")
        for f in patient_meta.fields:
             if any(x in str(f.label).lower() for x in ["table", "summary", "intake form", "form", "glp"]):
                print(f"STANDARD FIELD: {f.fieldname} ({f.label}) - Section: {f.get('section_break')}")

