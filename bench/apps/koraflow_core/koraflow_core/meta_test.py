import frappe

def execute():
    meta = frappe.get_meta('Patient')
    table_fields = [df.fieldname for df in meta.get("fields") if df.fieldtype == "Table"]
    print("Table fields on Patient:", table_fields)
    for fieldname in ['glp1_intake_forms', 'custom_medication_history', 'patient_relation']:
        df = meta.get_field(fieldname)
        print(f"DocField {fieldname}: {df is not None}")
