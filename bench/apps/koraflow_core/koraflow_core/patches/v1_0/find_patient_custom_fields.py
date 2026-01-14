import frappe

def execute():
    fields = frappe.db.get_all("Custom Field", 
        filters={"dt": "Patient"}, 
        fields=["name", "fieldname", "label", "fieldtype", "insert_after", "hidden"],
        order_by="idx asc" # Though idx in Custom Field isn't always reliable for order
    )
    print("CUSTOM FIELDS ON PATIENT:")
    for f in fields:
        print(f)
