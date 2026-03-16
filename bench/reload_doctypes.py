
import frappe

def reload_schemas():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("Reloading GLP-1 Intake Submission...")
    frappe.reload_doc("koraflow_core", "doctype", "glp1_intake_submission")
    
    print("Reloading Intake Form Print Format...")
    frappe.reload_doc("koraflow_core", "print_format", "intake_form")
    
    print("Reload Complete.")

if __name__ == "__main__":
    reload_schemas()
