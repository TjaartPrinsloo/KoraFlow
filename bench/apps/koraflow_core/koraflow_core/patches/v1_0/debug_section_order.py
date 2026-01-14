import frappe

def execute():
    fields = frappe.db.get_all("Custom Field", 
        filters={"dt": "Patient", "fieldname": ["in", ["section_glp1_forms_visible", "glp1_intake_forms", "ai_medical_summary", "planning_to_conceive"]]}, 
        fields=["fieldname", "label", "fieldtype", "insert_after", "hidden"],
    )
    print("VISIBILITY & ORDER CHECK:")
    for f in fields:
        print(f)
