import frappe

def fix_card_standard():
    card_name = "Patient Pending Clinical Review"
    if frappe.db.exists("Number Card", card_name):
        frappe.db.set_value("Number Card", card_name, "is_standard", 0)
        frappe.db.commit()
        frappe.clear_cache()
        print(f"Set '{card_name}' to non-standard and cleared cache.")
    else:
        print(f"Card '{card_name}' not found.")

if __name__ == "__main__":
    fix_card_standard()
