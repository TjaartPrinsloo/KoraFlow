import frappe

def execute():
    fields = frappe.db.get_all("Custom Field", 
        filters={"dt": "Patient", "fieldname": ["in", ["section_key_biometrics", "intake_height_cm", "bmi", "weight_to_lose"]]}, 
        fields=["fieldname", "label", "fieldtype", "insert_after", "hidden"],
    )
    print("BIOMETRICS CHECK:")
    for f in fields:
        print(f)
