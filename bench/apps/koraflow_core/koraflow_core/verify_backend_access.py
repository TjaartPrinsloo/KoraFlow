
import frappe

def verify_and_fix():
    print("Verifying Sales Agent backend access...")
    
    # 1. Check Module in DB
    
    # 0. Check Patient Referral (Reference)
    pr_module = frappe.db.get_value("DocType", "Patient Referral", "module")
    print(f"Patient Referral Module in DB: {pr_module}")
    try:
        # Just check if we can get the controller class
        from frappe.model.base_document import get_controller
        ctrl = get_controller("Patient Referral")
        print(f"SUCCESS: Loaded Patient Referral controller: {ctrl}")
    except Exception as e:
        print(f"FAILURE: Patient Referral controller load failed: {e}")

    # 1. Update Module in DB to try to match if needed
    if pr_module and pr_module != module:
        print(f"Updating Sales Agent DB module from '{module}' to '{pr_module}'")
        frappe.db.set_value("DocType", "Sales Agent", "module", pr_module)
        frappe.db.commit()
        frappe.clear_cache()
    
    # 2. Try to load doc or create it
    try:
        # Check if agent profile exists
        name = frappe.db.get_value("Sales Agent", {"user": "test.sales.agent@koraflow.com"}, "name")
        if name:
            doc = frappe.get_doc("Sales Agent", name)
            print("SUCCESS: Loaded Sales Agent doc")
        else:
            print("WARNING: Sales Agent doc still not found. Try creating manually in Desk.")
            
    except Exception as e:
        print(f"FAILURE: {e}")

verify_and_fix()
