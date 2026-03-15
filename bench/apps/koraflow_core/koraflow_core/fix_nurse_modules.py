import frappe

def fix_nurse_modules():
    frappe.flags.in_patch = True
    users = frappe.get_all("Has Role", filters={"role": "Nurse", "parenttype": "User"}, fields=["parent"])
    
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    allowed_modules = ["Healthcare"]
    expected_blocks = [m for m in all_modules if m not in allowed_modules]
    
    for u in users:
        print(f"Fixing {u.parent}")
        doc = frappe.get_doc("User", u.parent)
        
        current_blocks = [m.module for m in doc.get("block_modules", [])]
        
        if set(expected_blocks) != set(current_blocks):
            doc.set("block_modules", [{"module": m} for m in expected_blocks])
            doc.flags.in_nurse_update = True
            doc.flags.ignore_permissions = True
            doc.save()
            print(f"  Saved blocked modules for {u.parent}")
        else:
            print(f"  Blocked modules already correct for {u.parent}")

        
    frappe.flags.in_patch = False
    frappe.db.commit()

if __name__ == "__main__":
    fix_nurse_modules()
