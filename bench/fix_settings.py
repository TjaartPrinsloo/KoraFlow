
import frappe
frappe.init(site="koraflow-site")
frappe.connect()
try:
    frappe.db.set_value('Website Settings', 'Website Settings', 'home_page', 'login')
    frappe.db.commit()
    print("Home page set to s2w_login")
except Exception as e:
    print(f"Error: {e}")
