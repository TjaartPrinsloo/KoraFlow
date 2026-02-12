import frappe
from frappe.utils import today

def create_data():
    frappe.set_user("Administrator")
    
    user_email = "test_user_67890@koraflow.com"
    first_name = "Test User"
    
    # 1. Ensure User exists
    if not frappe.db.exists("User", user_email):
        user = frappe.new_doc("User")
        user.email = user_email
        user.first_name = first_name
        user.enabled = 1
        user.insert(ignore_permissions=True)
        print(f"Created User: {user_email}")
    else:
        print(f"User exists: {user_email}")

    # 2. Ensure Patient exists
    patient_name = frappe.db.get_value("Patient", {"email": user_email}, "name")
    if not patient_name:
        p = frappe.new_doc("Patient")
        p.first_name = first_name
        p.email = user_email
        p.user = user_email # Link to user
        p.status = "Active"
        p.dob = "1990-01-01"
        p.sex = "Male"
        p.mobile = "+27123456789"
        p.insert(ignore_permissions=True)
        patient_name = p.name
        print(f"Created Patient: {patient_name}")
    else:
        print(f"Patient exists: {patient_name}")

    # 3. Ensure Customer exists
    customer_name = frappe.db.get_value("Patient", patient_name, "customer")
    if not customer_name:
        # Check if customer with same name exists
        if frappe.db.exists("Customer", patient_name):
            cust = frappe.get_doc("Customer", patient_name)
        else:
            cust = frappe.new_doc("Customer")
            cust.customer_name = patient_name
            cust.customer_type = "Individual"
            cust.customer_group = "All Customer Groups"
            cust.territory = "All Territories"
            cust.insert(ignore_permissions=True)
        
        frappe.db.set_value("Patient", patient_name, "customer", cust.name)
        customer_name = cust.name
        print(f"Linked Customer: {customer_name}")
    else:
        print(f"Customer exists: {customer_name}")
        
    # 4. Create Quotation (Open)
    # Check if open quotation exists
    existing_qt = frappe.db.get_value("Quotation", {"party_name": customer_name, "status": "Open", "docstatus": 1})
    if existing_qt:
        print(f"Existing Open Quotation: {existing_qt}")
    else:
        # Need an item
        item_code = "Consultation"
        if not frappe.db.exists("Item", item_code):
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_group = "All Item Groups"
            item.stock_uom = "Nos"
            item.is_stock_item = 0
            item.insert(ignore_permissions=True)
            
        qt = frappe.new_doc("Quotation")
        qt.quotation_to = "Customer"
        qt.party_name = customer_name
        qt.transaction_date = today()
        qt.append("items", {
            "item_code": item_code,
            "qty": 1,
            "rate": 500.0,
            "uom": "Nos"
        })
        qt.save(ignore_permissions=True)
        qt.submit()
        print(f"Created & Submitted Quotation: {qt.name}")

if __name__ == "__main__":
    frappe.init("koraflow-site", sites_path="sites")
    frappe.connect()
    create_data()
    frappe.db.commit()
