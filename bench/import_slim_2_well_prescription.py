import frappe
from frappe.modules.import_file import import_doc

def execute():
    site = "koraflow-site"
    frappe.init(site=site)
    frappe.connect()
    
    file_path = "apps/koraflow_core/koraflow_core/print_format/slim_2_well_prescription/slim_2_well_prescription.json"
    
    try:
        print(f"Importing {file_path}...")
        import_doc(file_path)
        frappe.db.commit()
        print("Successfully imported Slim 2 Well Prescription print format.")
    except Exception as e:
        print(f"Error importing print format: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    execute()
