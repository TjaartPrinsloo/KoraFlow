import frappe
from koraflow_core.utils.patient_sync import sync_intake_to_patient

def fix():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("--- FIXING JANELIE ---")
    try:
        doc = frappe.get_doc("Patient", "Janelie")
        
        # 1. Populate missing source data in Child Table for testing
        if doc.glp1_intake_forms:
             row = doc.glp1_intake_forms[-1]
             
             # Set Blood Group if missing (Handle Schema lag)
             if not row.get("blood_group"):
                 try:
                     row.db_set("blood_group", "O+")
                     print("Set Dummy Blood Group: O+")
                 except Exception as e:
                     print(f"Skipping Blood Group: {e}")
                 
             # Set Mobile
             if not row.get("mobile"):
                 try:
                     row.db_set("mobile", "+27821234567")
                     print("Set Dummy Mobile: +27821234567")
                 except Exception as e:
                    print(f"Skipping Mobile: {e}")

        # 2. Force Sync
        # Reload doc
        doc.reload()
        sync_intake_to_patient(doc, "manual_fix")
        frappe.db.commit()
        print("Sync Completed.")
        
        # 3. Verify
        doc.reload()
        print(f"Verified Patient Values:")
        print(f" - DOB: {doc.dob}")
        print(f" - Sex: {doc.sex}")
        print(f" - Custom SA ID: {doc.custom_sa_id_number}")
        print(f" - Goal Weight: {doc.intake_goal_weight}")
        print(f" - Blood Group: {doc.blood_group}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

fix()
