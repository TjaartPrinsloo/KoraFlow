import frappe

def test_quote():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n--- QUOTATION GEN TEST START ---")
    try:
        # 1. Get a Patient
        patient = frappe.get_doc("Patient", "Janelie")
        print(f"Patient: {patient.name}, Customer: {patient.customer}")
        
        # 2. Get a Medication (use first available or create test)
        meds = frappe.get_all("Medication", limit=1)
        if not meds:
            print("No Medication found! Creating one...")
            item = frappe.get_doc({"doctype": "Item", "item_code": "TEST-MED", "item_group": "Products", "is_stock_item": 0}).insert(ignore_permissions=True)
            med = frappe.get_doc({"doctype": "Medication", "medication_name": "Test Med", "item": item.name}).insert(ignore_permissions=True)
            med_name = med.name
        else:
            med_name = meds[0].name
            
        print(f"Using Medication: {med_name}")
        # Check Item validity (via child table)
        linked = frappe.get_all("Medication Linked Item", filters={"parent": med_name}, fields=["item"], limit=1)
        item_code = linked[0].item if linked else None
        print(f"Linked Item Code: {item_code}")
        
        if not item_code:
            print("ERROR: Medication has no linked Item! Quotation logic will fail.")
            
        # 3. Check Company
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        print(f"Default Company: {company}")
        if not company:
            # Try to find ANY company
            c = frappe.get_all("Company", limit=1)
            if c:
                print(f"Found Company in DB: {c[0].name}")
            else:
                print("ERROR: No Company found in system!")

        # 4. Create Prescription
        print("Creating Prescription...")
        # Need a doctor?
        doc_reg = "12345" 
        # Find valid doctor
        docs = frappe.get_all("Healthcare Practitioner", limit=1)
        doctor = docs[0].name if docs else None
        print(f"Using Doctor: {doctor}")
        
        pres = frappe.new_doc("GLP-1 Patient Prescription")
        pres.patient = patient.name
        pres.medication = med_name
        pres.doctor = doctor
        pres.dosage = "5mg"
        pres.quantity = 1
        pres.duration = "1 Month"
        pres.doctor_registration_number = doc_reg
        pres.status = "Draft"
        pres.insert(ignore_permissions=True)
        print(f"Prescription Created: {pres.name}")
        
        # 5. Submit (Trigger on_submit)
        print("Submitting Prescription...")
        pres.submit()
        print(f"Prescription Status: {pres.status}")
        
        # 6. Check Quotation
        pres.reload()
        print(f"Linked Quotation: {pres.linked_quotation}")
        
        if pres.linked_quotation:
            q = frappe.get_doc("Quotation", pres.linked_quotation)
            print(f"Quotation Created: {q.name}, Total: {q.grand_total}")
            print("SUCCESS")
        else:
            print("FAILURE: Linked Quotation is Empty.")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

test_quote()
