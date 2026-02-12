
import frappe

def get_latest_error():
    try:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()
        
        # Get latest error log
        errors = frappe.get_all("Error Log", fields=["name", "error", "method", "seen"], order_by="creation desc", limit=1)
        
        if errors:
            error_doc = frappe.get_doc("Error Log", errors[0].name)
            print("=== LATEST ERROR LOG ===")
            print(f"Method: {error_doc.method}")
            print(f"Error: \n{error_doc.error}")
        else:
            print("No error logs found.")
            
    except Exception as e:
        print(f"Failed to fetch error log: {e}")

if __name__ == "__main__":
    get_latest_error()
