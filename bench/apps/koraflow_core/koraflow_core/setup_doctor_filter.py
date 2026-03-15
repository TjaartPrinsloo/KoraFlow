import frappe
import json

def create_doctor_filter():
    frappe.flags.in_patch = True
    
    # Try to find existing
    existing = frappe.db.exists("List Filter", {"reference_doctype": "Patient Encounter", "filter_name": "Awaiting Doctor Sign-Off"})
    
    if not existing:
        doc = frappe.get_doc({
            "doctype": "List Filter",
            "reference_doctype": "Patient Encounter",
            "filter_name": "Awaiting Doctor Sign-Off",
            "is_default": 0,
            "filters": json.dumps([
                ["Patient Encounter", "docstatus", "=", 0, False]
            ])
        })
        doc.insert(ignore_permissions=True)
        print("Created List Filter: Awaiting Doctor Sign-Off")
    else:
        print("Filter already exists.")

    frappe.flags.in_patch = False
    frappe.db.commit()

if __name__ == "__main__":
    create_doctor_filter()
