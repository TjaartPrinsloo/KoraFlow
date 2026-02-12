import frappe

def debug():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n--- DATA CHECK START ---")
    try:
        doc = frappe.get_doc("Patient", "Janelie")
        if not doc.glp1_intake_forms:
            print("No Intake Forms found.")
            return

        row = doc.glp1_intake_forms[-1]
        print(f"Intake Row: {row.name}")
        
        # Check values
        print(f"blood_group: '{row.get('blood_group')}'")
        print(f"mobile: '{row.get('mobile')}'")
        print(f"last_name: '{row.get('last_name')}'")
        print(f"sa_id_number: '{row.get('sa_id_number')}'")
        print(f"dob: '{row.get('dob')}'")
        print(f"intake_goal_weight: '{row.get('intake_goal_weight')}'")
        
    except Exception as e:
        print(f"ERROR: {e}")
        
    print("--- DATA CHECK END ---\n")

debug()
