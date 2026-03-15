import frappe

def v3_fix():
    user_email = "nurse@koraflow.com"
    ws_name = "Nurse Workcenter"
    
    # 1. Create/Update Workspace
    if frappe.db.exists("Workspace", ws_name):
        ws = frappe.get_doc("Workspace", ws_name)
    else:
        ws = frappe.new_doc("Workspace")
        ws.name = ws_name
        ws.label = ws_name
        ws.title = ws_name

        
    ws.module = "Healthcare"
    ws.parent_page = None
    ws.public = 1
    ws.is_hidden = 0
    ws.sequence_id = -100 # Put it at the top
    
    ws.set("shortcuts", [])
    ws.append("shortcuts", {"type": "DocType", "link_to": "Patient", "label": "All Patients", "icon": "user"})
    ws.append("shortcuts", {"type": "DocType", "link_to": "Patient Encounter", "label": "Encounters", "icon": "file"})
    ws.append("shortcuts", {"type": "DocType", "link_to": "Vital Signs", "label": "Vital Signs", "icon": "pulse"})
    
    ws.set("roles", [])
    ws.append("roles", {"role": "Nurse"})
    
    ws.flags.ignore_permissions = True
    ws.save()
    frappe.db.commit()
    print(f"Created/Updated Workspace: {ws_name}")

    # 2. Force Blocked Modules
    user = frappe.get_doc("User", user_email)
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    
    # Block EVERYTHING EXCEPT Healthcare
    to_block = [m for m in all_modules if m != "Healthcare"]
    
    # Use doc.set to ensure it replaces everything
    user.set("block_modules", [{"module": m} for m in to_block])
    
    user.flags.ignore_permissions = True
    user.flags.in_nurse_update = True
    user.save()

    
    # 3. Set Default Workspace
    frappe.db.set_value("User", user_email, "default_workspace", ws_name)
    frappe.db.commit()
    
    frappe.clear_cache(user=user_email)
    frappe.clear_cache()
    print("Done. Caches cleared.")

if __name__ == "__main__":
    v3_fix()
