import frappe

def check_logs():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n--- CHECKING ERROR LOGS ---")
    try:
        # Get last 5 logs for 'Quotation Debug'
        logs = frappe.get_all("Error Log", 
                             filters={"method": "Quotation Debug"}, 
                             fields=["creation", "error"], 
                             order_by="creation desc", 
                             limit=5)
                             
        if not logs:
            print("No 'Quotation Debug' logs found! The code might not have triggered at all.")
        else:
            for log in logs:
                print(f"[{log.creation}] {log.error}")
                
    except Exception as e:
        print(f"Error: {e}")

check_logs()
