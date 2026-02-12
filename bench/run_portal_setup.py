
import frappe
from frappe.utils import add_days, nowdate, nowtime

def setup():
    print("Starting test data setup via bench shell...")
    email = "test_patient@example.com"
    first_name = "Test"
    last_name = "Patient"
    
    if not frappe.db.exists("User", email):
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.send_welcome_email = 0
        user.save(ignore_permissions=True)
        user.add_roles("Patient")
        print(f"Created User: {email}")
    else:
        print(f"User exists: {email}")
    
    customer_name = "Test Patient Customer"
    if not frappe.db.exists("Customer", customer_name):
        customer = frappe.new_doc("Customer")
        customer.customer_name = customer_name
        customer.customer_type = "Individual"
        customer.customer_group = "All Customer Groups"
        customer.territory = "All Territories"
        customer.save(ignore_permissions=True)
        print(f"Created Customer: {customer_name}")
    
    patient_name = frappe.db.get_value("Patient", {"email": email}, "name")
    if not patient_name:
        patient = frappe.new_doc("Patient")
        patient.first_name = first_name
        patient.last_name = last_name
        patient.email = email
        patient.sex = "Female"
        patient.dob = "1990-01-01"
        patient.customer = customer_name
        patient.mobile_number = "+27821234567"
        patient.address_line1 = "123 Test St"
        patient.city = "Cape Town"
        patient.save(ignore_permissions=True)
        patient_name = patient.name
        print(f"Created Patient: {patient_name}")
    else:
        frappe.db.set_value("Patient", patient_name, "customer", customer_name)
        print(f"Patient exists: {patient_name}")

    if not frappe.db.exists("Patient Vital", {"patient": patient_name}):
        vital = frappe.new_doc("Patient Vital")
        vital.patient = patient_name
        vital.date = nowdate()
        vital.time = nowtime()
        vital.weight_kg = 85.5
        vital.height_cm = 170
        vital.save(ignore_permissions=True)
        print("Created Patient Vital")

    if frappe.db.exists("DocType", "GLP-1 Patient Prescription"):
        prescriptions = frappe.get_all("GLP-1 Patient Prescription", filters={"patient": patient_name})
        if not prescriptions:
            pres = frappe.new_doc("GLP-1 Patient Prescription")
            pres.patient = patient_name
            pres.medication = "Semaglutide"
            pres.dosage = "0.25mg"
            pres.status = "Active"
            pres.prescription_date = nowdate()
            pres.expiry_date = add_days(nowdate(), 30)
            pres.doctor = "Dr. Test"
            pres.doctor_registration_number = "MP123456"
            pres.save(ignore_permissions=True)
            print("Created Prescription")

    if frappe.db.exists("DocType", "GLP-1 Shipment"):
        shipments = frappe.get_all("GLP-1 Shipment", filters={"patient": patient_name})
        if not shipments:
            ship = frappe.new_doc("GLP-1 Shipment")
            ship.patient = patient_name
            ship.status = "Out for Delivery"
            ship.courier_reference = "CR123456"
            ship.tracking_url = "http://track.me/CR123456"
            ship.waybill_number = "WB998877"
            ship.save(ignore_permissions=True)
            print("Created Shipment")

    # Ensure Item
    if not frappe.db.exists("Item", "GLP1-025"):
        item = frappe.new_doc("Item")
        item.item_code = "GLP1-025"
        item.item_name = "GLP-1 Starter Kit"
        item.item_group = "All Item Groups"
        item.save(ignore_permissions=True)

    quotes = frappe.get_all("Quotation", filters={"party_name": customer_name, "status": "Open", "docstatus": 0})
    if not quotes:
        try:
            quote = frappe.new_doc("Quotation")
            quote.quotation_to = "Customer"
            quote.party_name = customer_name
            quote.transaction_date = nowdate()
            quote.append("items", {
                "item_code": "GLP1-025", 
                "item_name": "GLP-1 Starter Kit",
                "qty": 1,
                "rate": 1500
            })
            quote.save(ignore_permissions=True)
            print("Created Quotation")
        except Exception as e:
            print(f"Failed to create quote: {e}")

    # Check Invoice
    invoices = frappe.get_all("Sales Invoice", filters={"customer": customer_name})
    if not invoices:
        try:
            inv = frappe.new_doc("Sales Invoice")
            inv.customer = customer_name
            inv.posting_date = add_days(nowdate(), -10)
            inv.due_date = nowdate()
            inv.append("items", {
                "item_code": "GLP1-025",
                "qty": 1,
                "rate": 1500
            })
            inv.save(ignore_permissions=True)
            inv.submit()
            print("Created Sales Invoice")
        except Exception as e:
            print(f"Failed to create invoice: {e}")

    frappe.db.commit()
    print("Test Data Setup Link Complete.")

setup()
