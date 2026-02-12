import frappe

def fix_blood_group():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("--- FIXING BLOOD GROUP ---")
    try:
        # Fix Patient Record directly
        print("Updating Patient 'Janelie'...")
        frappe.db.set_value("Patient", "Janelie", "blood_group", "O Positive")
        
        # Fix Intake Form Row (So next sync doesn't revert to O+)
        doc = frappe.get_doc("Patient", "Janelie")
        if doc.glp1_intake_forms:
            row = doc.glp1_intake_forms[-1]
            # Verify if column exists first (it should now)
            if row.get("blood_group") == "O+":
                print("Updating Intake Row 'blood_group' to 'O Positive' (Wait, intake form allows O+?)")
                # Actually, Intake Form DocType was set to "A+\nA-..." options in Step 967.
                # So Intake Form EXPECTS "O+".
                # BUT Patient EXPECTS "O Positive".
                # My sync logic (just updated) maps O+ -> O Positive.
                # So the Intake Form SHOULD be "O+".
                # The issue was that I synced "O+" directly to Patient.
                
                print("Intake form has O+, which is valid for Intake. Mapping logic fixes Patient.")
                
            else:
                 print(f"Intake Row blood_group is '{row.get('blood_group')}'.")
                 
        frappe.db.commit()
        print("Success: Patient Blood Group set to 'O Positive'.")
        
    except Exception as e:
        print(f"Error: {e}")

fix_blood_group()
