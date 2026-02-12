import frappe

def execute():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()
    
    table = "GLP-1 Intake Submission"
    column = "blood_group"
    
    try:
        print(f"Checking column '{column}' in '{table}'...")
        if not frappe.db.has_column(table, column):
            print("Adding blood_group column via SQL...")
            frappe.db.sql(f"ALTER TABLE `tab{table}` ADD COLUMN `{column}` varchar(10)")
            frappe.db.commit()
            print("Success: Column added.")
        else:
            print("Column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")

execute()
