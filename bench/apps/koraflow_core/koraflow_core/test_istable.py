import frappe
def check_istable():
    print("GLP-1 Intake Form istable in DB:", frappe.db.get_value("DocType", "GLP-1 Intake Form", "istable"))
    print("GLP-1 Intake Submission istable in DB:", frappe.db.get_value("DocType", "GLP-1 Intake Submission", "istable"))
    print("Patient Medication Entry istable in DB:", frappe.db.get_value("DocType", "Patient Medication Entry", "istable"))
    
    # Check if there are any child table fields on Patient that reference these
    links = frappe.db.get_all("DocField", filters={"options": ["in", ["GLP-1 Intake Form", "GLP-1 Intake Submission"]]}, fields=["parent", "fieldname", "fieldtype"])
    print("DocFields linking to intake forms:", links)
    
    custom_links = frappe.db.get_all("Custom Field", filters={"options": ["in", ["GLP-1 Intake Form", "GLP-1 Intake Submission"]]}, fields=["dt", "fieldname", "fieldtype"])
    print("Custom Fields linking to intake forms:", custom_links)
