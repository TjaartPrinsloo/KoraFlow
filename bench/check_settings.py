import frappe
import os

frappe.init(site="koraflow-site")
frappe.connect()
try:
    val = frappe.db.get_single_value('Website Settings', 'home_page')
    print(f"Home Page: {val}")
    
    # Check installed apps
    apps = frappe.get_installed_apps()
    print(f"Installed Apps: {apps}")
except Exception as e:
    print(f"Error: {e}")
