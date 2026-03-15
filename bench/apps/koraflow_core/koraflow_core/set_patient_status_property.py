import frappe

def create_patient_status_property_setter():
    frappe.make_property_setter({
        "doctype": "Patient",
        "fieldname": "status",
        "property": "options",
        "value": "Active\nDisabled\nUnder Review",
        "property_type": "Select"
    })
    frappe.db.commit()
    print("Property Setter created for Patient status.")

if __name__ == "__main__":
    create_patient_status_property_setter()
