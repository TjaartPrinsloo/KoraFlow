import frappe

def fix_page_perm():
    frappe.flags.in_patch = True
    
    # Check if a custom docperm already exists for Nurse on Page
    exists = frappe.db.exists("Custom DocPerm", {"parent": "Page", "role": "Nurse"})
    if not exists:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = "Page"
        doc.parenttype = "DocType"
        doc.parentfield = "permissions"
        doc.role = "Nurse"
        doc.read = 1
        doc.insert(ignore_permissions=True)
        print("Added Custom DocPerm for Nurse on Page")
    else:
        doc = frappe.get_doc("Custom DocPerm", exists)
        doc.read = 1
        doc.save(ignore_permissions=True)
        print("Updated Custom DocPerm for Nurse on Page")
        
    frappe.db.commit()
    
if __name__ == "__main__":
    fix_page_perm()
