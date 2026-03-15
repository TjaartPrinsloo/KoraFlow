import frappe

def fix_nurse_workspace_and_modules():
    user_email = "nurse@koraflow.com"
    ws_name = "Nurse Dashboard"
    
    # 1. Setup Nurse Dashboard Workspace
    if frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc("Workspace", ws_name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.name = ws_name
        doc.label = ws_name
        
    doc.module = "Healthcare"
    doc.public = 1
    doc.is_hidden = 0
    doc.parent_page = None
    
    # Clear existing links/shortcuts
    doc.set("links", [])
    doc.set("shortcuts", [])
    
    # Add Patient shortcut
    doc.append("shortcuts", {
        "type": "DocType",
        "link_to": "Patient",
        "label": "Patients",
        "icon": "user"
    })
    
    # Add Patient Encounter shortcut
    doc.append("shortcuts", {
        "type": "DocType",
        "link_to": "Patient Encounter",
        "label": "Patient Encounters",
        "icon": "folder"
    })
    
    # Add Role restriction
    if not any(r.role == "Nurse" for r in doc.get("roles", [])):
        doc.append("roles", {"role": "Nurse"})
        
    doc.flags.ignore_permissions = True
    doc.save()
    print(f"Updated Workspace: {ws_name}")
    
    # 2. Fix User Blocked Modules
    user = frappe.get_doc("User", user_email)
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    
    # We want Healthcare to be allowed.
    # We also need 'Core', 'Desk', 'Setup' etc to be allowed for basic Frappe UI?
    # Actually, let's just block the ones the user explicitly mentioned or the ones that are annoying.
    # The user wants to hide Xero and Courier Guy (KoraFlow Core module).
    
    to_block = [m for m in all_modules if m not in ["Healthcare", "Desk", "Core", "Setup", "KoraFlow Core"]]
    # Wait, if I allow KoraFlow Core, Xero and Courier Guy show up.
    # So I MUST block KoraFlow Core.
    
    to_block = [m for m in all_modules if m not in ["Healthcare", "Desk", "Core", "Setup"]]
    
    print(f"Blocking {len(to_block)} modules for {user_email}...")
    user.set("block_modules", [{"module": m} for m in to_block])
    user.flags.ignore_permissions = True
    user.flags.in_nurse_update = True
    user.save()
    
    frappe.db.commit()
    frappe.clear_cache(user=user_email)
    print(f"Fixed modules for {user_email}")

if __name__ == "__main__":
    fix_nurse_workspace_and_modules()
