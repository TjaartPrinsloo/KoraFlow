
import frappe

def execute():
    try:
        user_email = "test_sales_agent@koraflow.io"
        if frappe.db.exists("User", user_email):
            user = frappe.get_doc("User", user_email)
            user.new_password = "KoraFlowTest123!"
            user.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"Password for {user_email} set to 'KoraFlowTest123!'")
        else:
            print(f"User {user_email} not found")
    except Exception as e:
        print(f"Error setting password: {e}")
