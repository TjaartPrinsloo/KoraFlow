import frappe

def final_fix():
    user_email = "nurse@koraflow.com"
    user = frappe.get_doc("User", user_email)
    
    # Check all modules
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    
    # We want ONLY Healthcare to be allowed
    to_block = [m for m in all_modules if m != "Healthcare"]
    
    print(f"Assigning {len(to_block)} to block list for {user_email}")
    user.set("block_modules", [{"module": m} for m in to_block])
    
    user.flags.ignore_permissions = True
    user.flags.in_nurse_update = True
    user.save()
    
    # Verify
    user.reload()
    blocks = [m.module for m in user.block_modules]
    if "Healthcare" in blocks:
        print("CRITICAL: Healthcare is STILL in block list!")
        # Force delete from DB
        frappe.db.sql("DELETE FROM `tabBlock Module` WHERE parent=%s AND module='Healthcare'", user_email)
        frappe.db.commit()
    
    print(f"Final Blocks for {user_email}: {len(blocks)}")
    
    # Fix Workspace Nurse Dashboard
    ws = frappe.get_doc("Workspace", "Nurse Dashboard")
    ws.module = "Healthcare"
    ws.parent_page = None
    ws.public = 1
    
    # Ensure it's not hidden
    ws.is_hidden = 0
    
    # Add items if empty
    if not ws.shortcuts:
        ws.append("shortcuts", {"type": "DocType", "link_to": "Patient", "label": "Patients", "icon": "user"})
        ws.append("shortcuts", {"type": "DocType", "link_to": "Patient Encounter", "label": "Encounters", "icon": "file"})
        ws.append("shortcuts", {"type": "DocType", "link_to": "Vital Signs", "label": "Vital Signs", "icon": "pulse"})
        
    ws.flags.ignore_permissions = True
    ws.save()
    frappe.db.commit()
    
    # Clear Cache
    frappe.clear_cache()
    print("All caches cleared.")

if __name__ == "__main__":
    final_fix()
