
import frappe

def run():
    user = "test.patient.new.456@example.com"
    profile_name = "Patient Module Profile"
    
    # 1. Ensure Module Profile exists
    if not frappe.db.exists("Module Profile", profile_name):
        mp = frappe.new_doc("Module Profile")
        mp.module_profile_name = profile_name
        mp.append("block_modules", {"module": "Drive"})
        mp.insert(ignore_permissions=True)
        print(f"Created Module Profile: {profile_name}")
    else:
        # Update existing profile to ensure Drive is blocked
        mp = frappe.get_doc("Module Profile", profile_name)
        drive_blocked = False
        for blocked in mp.block_modules:
            if blocked.module == "Drive":
                drive_blocked = True
                break
        
        if not drive_blocked:
            mp.append("block_modules", {"module": "Drive"})
            mp.save(ignore_permissions=True)
            print(f"Updated Module Profile: {profile_name} to block Drive")

    # 2. Assign to User
    user_doc = frappe.get_doc("User", user)
    user_doc.flags.ignore_password_policy = True
    user_doc.module_profile = profile_name
    user_doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Assigned {profile_name} to user {user}")

if __name__ == "__main__":
    run()
else:
    run()
