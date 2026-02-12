
import frappe

def reload_schemas():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("Reloading GLP-1 Intake Form...")
    frappe.reload_doc("koraflow_core", "doctype", "glp1_intake_form")
    
    print("Reloading Healthcare Patient...")
    frappe.reload_doc("healthcare", "doctype", "patient")
    
    print("Reloading ERPNext Quotation...")
    frappe.reload_doc("selling", "doctype", "quotation")
    
    print("Reload Complete.")

if __name__ == "__main__":
    reload_schemas()
