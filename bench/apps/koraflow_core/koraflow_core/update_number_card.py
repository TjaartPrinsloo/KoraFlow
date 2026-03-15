import frappe

def update_number_card():
    old_name = "Total Patients Admitted"
    new_name = "Patient Pending Clinical Review"
    
    if frappe.db.exists("Number Card", old_name):
        frappe.db.set_value("Number Card", old_name, "label", new_name)
        frappe.rename_doc("Number Card", old_name, new_name, force=True)
        frappe.db.commit()
        print(f"Renamed Number Card from '{old_name}' to '{new_name}' and updated label.")
    else:
        print(f"Number Card '{old_name}' not found.")

if __name__ == "__main__":
    update_number_card()
