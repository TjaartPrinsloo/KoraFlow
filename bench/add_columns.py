
import frappe
from frappe.database.schema import add_column

def add_missing_columns():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("Adding columns to Patient...")
    try:
        add_column("Patient", "custom_referrer_name", "Data")
        print("Added custom_referrer_name to Patient")
    except Exception as e:
        print(f"Patient Error: {e}")

    print("Adding columns to GLP-1 Intake Form...")
    try:
        add_column("GLP-1 Intake Form", "custom_referrer_name", "Data")
        print("Added custom_referrer_name to GLP-1 Intake Form")
    except Exception as e:
        print(f"Intake Form Error: {e}")

    print("Adding columns to Quotation...")
    try:
        add_column("Quotation", "custom_referrer_name", "Data")
        print("Added custom_referrer_name to Quotation")
    except Exception as e:
        print(f"Quotation Referrer Error: {e}")
        
    try:
        add_column("Quotation", "custom_sales_agent", "Link")
        print("Added custom_sales_agent to Quotation")
    except Exception as e:
        print(f"Quotation Sales Agent Error: {e}")

    try:
        add_column("Quotation", "custom_prescription", "Link")
        print("Added custom_prescription to Quotation")
    except Exception as e:
        print(f"Quotation Prescription Error: {e}")

    frappe.db.commit()
    print("Column addition complete.")

if __name__ == "__main__":
    add_missing_columns()
