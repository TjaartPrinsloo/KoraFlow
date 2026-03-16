import frappe
from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings

def fix():
    for email in ["sr.lee@koraflow.com", "andre.terblanche@koraflow.com", "marinda.scharneck@koraflow.com"]:
        if not frappe.db.exists("Notification Settings", email):
            create_notification_settings(email)
            print(f"Created Notification Settings for {email}")
        else:
            print(f"Notification Settings already exists for {email}")
    frappe.db.commit()

if __name__ == "__main__":
    fix()
