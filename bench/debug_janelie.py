import frappe
from frappe import _
import os

def debug():
    # Init Frappe
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n--- DEBUG START ---")
    try:
        # Get Patient
        doc = frappe.get_doc("Patient", "Janelie")
        print(f"Patient Found: {doc.name}")
        
        # Check Custom Fields
        print("\nChecking Fields on Patient DocType:")
        meta = frappe.get_meta("Patient")
        fields = [df.fieldname for df in meta.fields]
        print(f"Has 'intake_weight_kg': {'intake_weight_kg' in fields}")
        print(f"Has 'weight_kg': {'weight_kg' in fields}")
        print(f"Has 'glp1_intake_forms': {'glp1_intake_forms' in fields}")
        
        # Check Values
        print("\nCurrent Values:")
        print(f"intake_weight_kg: {doc.get('intake_weight_kg')}")
        print(f"UID: {doc.get('uid')}")
        
        # Check Child Table
        print("\nChild Table 'glp1_intake_forms':")
        if not doc.get("glp1_intake_forms"):
            print("EMPTY/NONE")
        else:
            for row in doc.glp1_intake_forms:
                print(f"Row {row.idx}: {row.name}")
                print(f" - intake_weight_kg: {row.get('intake_weight_kg')}")
                print(f" - sa_id_number: {row.get('sa_id_number')}")
                print(f" - DocType of Row: {row.doctype}")
                
        # Try Sync Logic Manually
        print("\nTesting Manual Sync Logic:")
        from koraflow_core.utils.patient_sync import sync_intake_to_patient
        sync_intake_to_patient(doc, "manual_debug")
        frappe.db.commit() # FORCE COMMIT
        
        doc.reload() # RELOAD FROM DB
        print("Sync Function Ran without error.")
        print(f"New intake_weight_kg: {doc.get('intake_weight_kg')}")
        print(f"New UID: {doc.get('uid')}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    print("--- DEBUG END ---\n")

debug()
