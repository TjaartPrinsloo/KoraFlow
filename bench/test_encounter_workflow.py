import frappe
from frappe.utils import today, now

def test_encounter_workflow():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()
        frappe.clear_cache()


    print("\n--- PATIENT ENCOUNTER QUOTATION TEST START ---")
    try:
        # 1. Get a Patient
        patient = frappe.get_doc("Patient", "Janelie")
        print(f"Patient: {patient.name}, Customer: {patient.customer}")
        
        # 2. Get a Medication
        meds = frappe.get_all("Medication", limit=1)
        if not meds:
            print("No Medication found! Creating one...")
            # Ensure Item exists first
            if not frappe.db.exists("Item", "TEST-MED"):
                item = frappe.get_doc({"doctype": "Item", "item_code": "TEST-MED", "item_group": "Products", "is_stock_item": 0}).insert(ignore_permissions=True)
            
            med = frappe.get_doc({"doctype": "Medication", "medication_name": "Test Med", "item": "TEST-MED"}).insert(ignore_permissions=True)
            med_name = med.name
        else:
            med_name = meds[0].name
            
        print(f"Using Medication: {med_name}")

        # Ensure Item Price exists for the linked item
        linked = frappe.get_all("Medication Linked Item", filters={"parent": med_name}, fields=["item"], limit=1)
        item_code = linked[0].item if linked else None
        
        if item_code:
            current_price = frappe.get_all("Item Price", filters={"item_code": item_code, "price_list": "Standard Selling"})
            if not current_price:
                print(f"Creating Price for Item {item_code}")
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "price_list": "Standard Selling",
                    "price_list_rate": 500
                }).insert(ignore_permissions=True)
        else:
             print("WARNING: No linked item found for medication")

        # 2.5 Ensure Patient has a linked User (Disabled)
        test_email = "janelie.test@example.com"
        if not frappe.db.exists("User", test_email):
            print(f"Creating Test User: {test_email}")
            user = frappe.new_doc("User")
            user.email = test_email
            user.first_name = "Janelie"
            user.last_name = "Test"
            user.enabled = 0 # Start disabled
            user.save(ignore_permissions=True)
        else:
            user = frappe.get_doc("User", test_email)
            if user.enabled:
                print("User already enabled, disabling for test...")
                user.enabled = 0
                user.save(ignore_permissions=True)
        
        # Link user to patient
        if patient.user_id != test_email:
            print(f"Linking User {test_email} to Patient {patient.name}")
            patient.user_id = test_email
            
        # Set Referrer Name on Patient for Test
        patient.custom_referrer_name = "Dr. Phil"
        patient.save(ignore_permissions=True)
        frappe.db.commit()
            
        print(f"Test User State: Enabled={user.enabled}")
        print(f"Test Patient Referrer: {patient.custom_referrer_name}")

        # 3. Create Patient Encounter
        print("Creating Patient Encounter...")
        
        # Find valid doctor
        docs = frappe.get_all("Healthcare Practitioner", limit=1)
        doctor = docs[0].name if docs else None
        print(f"Using Practitioner: {doctor}")
        
        encounter = frappe.new_doc("Patient Encounter")
        encounter.patient = patient.name
        encounter.practitioner = doctor
        encounter.encounter_date = today()
        encounter.encounter_time = now()
        
        # Add Drug Prescription
        encounter.append("drug_prescription", {
            "medication": med_name,
            "dosage": "0.2 ml",
            "period": "1 Month",
             "dosage_form": "Injection" 
        })
        
        encounter.insert(ignore_permissions=True)
        print(f"Encounter Created: {encounter.name}")
        
        # 4. Submit Encounter
        print("Submitting Encounter...")
        encounter.submit()
        print(f"Encounter Status: {encounter.status}")
        
        # 5. Verify Quotation Creation
        # Check for latest quotation for this customer created today
        # Since we don't have a direct link in encounter without custom field, we check via remarks or just latest for patient
        
        if patient.customer:
            quotation = frappe.get_all("Quotation", 
                filters={
                    "party_name": patient.customer, 
                    "transaction_date": today(),
                    "title": f"Prescription: {encounter.name}"
                },
                order_by="creation desc",
                limit=1
            )
            
            if quotation:
                q = frappe.get_doc("Quotation", quotation[0].name)
                print(f"SUCCESS: Quotation Created: {q.name}")
                print(f"Total: {q.grand_total}")
                print(f"Title: {q.title}")
                
                # Verify Referrer and Prescription Link
                if hasattr(q, "custom_referrer_name") and q.custom_referrer_name == "Dr. Phil":
                    print("SUCCESS: Referrer Name propagated to Quotation.")
                else:
                     print(f"FAILURE: Referrer Name mismatch. Expected 'Dr. Phil', got '{getattr(q, 'custom_referrer_name', 'MISSING')}'")
                     
                if hasattr(q, "custom_prescription") and q.custom_prescription == encounter.name:
                    print(f"SUCCESS: Prescription Linked correctly: {q.custom_prescription}")
                else:
                    print(f"FAILURE: Prescription Link mismatch. Expected {encounter.name}, got {getattr(q, 'custom_prescription', 'MISSING')}")
            else:
                print("FAILURE: No Quotation found linked to this encounter.")
        else:
            print("FAILURE: Patient has no customer linked, so no quotation could be created.")
            
        # 6. Verify User Activation
        user.reload()
        if user.enabled:
            print(f"SUCCESS: User {user.email} is now ENABLED.")
        else:
            print(f"FAILURE: User {user.email} is still DISABLED.")


    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encounter_workflow()
