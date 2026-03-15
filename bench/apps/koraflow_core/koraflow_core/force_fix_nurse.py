import frappe

def force_fix_nurse():
    user_email = "nurse@koraflow.com"
    doc = frappe.get_doc("User", user_email)
    
    print(f"Current blocked modules for {user_email}:")
    print([m.module for m in doc.block_modules])
    
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    
    # We want Healthcare to be ALLOWED. 
    # Everything else should be BLOCKED.
    expected_block_list = [m for m in all_modules if m != "Healthcare"]
    
    print(f"Assigning {len(expected_block_list)} modules to block list...")
    doc.set("block_modules", [{"module": m} for m in expected_block_list])
    
    doc.flags.ignore_permissions = True
    # Important: set this flag to avoid loop if hook is still buggy
    doc.flags.in_nurse_update = True 
    doc.save()
    frappe.db.commit()
    
    # Reload and verify
    doc.reload()
    final_blocks = [m.module for m in doc.block_modules]
    print(f"Final blocked modules for {user_email}:")
    print(final_blocks)
    print(f"Is Healthcare blocked? {'Healthcare' in final_blocks}")

if __name__ == "__main__":
    force_fix_nurse()
