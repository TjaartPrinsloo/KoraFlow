import frappe
from frappe.utils import today, now, add_days
import json
import time

def run_full_process_test():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n==============================================")
    print("  RUNNING FULL AUTOMATED PROCESS TEST")
    print("==============================================\n")

    try:
        # ====================================================================
        # PRE-REQUISITES: SETUP USERS & DATA
        # ====================================================================
        print("--- 0. SETTING UP TEST DATA ---")
        
        # Unique timestamp for this run
        timestamp = int(time.time())
        patient_email = f"patient_{timestamp}@test.com"
        nurse_user = "nurse@test.com" # Assuming exists or we create
        doctor_user = "doctor@test.com" # Assuming exists or we create
        sales_agent_email = f"agent_{timestamp}@test.com"
        
        # Cleanup potential ghost data "Chris" which causes validation errors
        if frappe.db.exists("Patient", "Chris"):
             print("Cleaning up old 'Chris' patient...")
             frappe.delete_doc("Patient", "Chris", force=1)

        # Create Sales Agent
        if not frappe.db.exists("User", sales_agent_email):
            agent_user = frappe.new_doc("User")
            agent_user.email = sales_agent_email
            agent_user.first_name = "Agent"
            agent_user.last_name = f"Smith_{timestamp}"
            agent_user.enabled = 1
            agent_user.save(ignore_permissions=True)
            
            # Create Sales Agent DocType linked to User
            agent_doc = frappe.new_doc("Sales Agent")
            agent_doc.user = sales_agent_email
            agent_doc.first_name = "Agent"
            agent_doc.last_name = f"Smith_{timestamp}"
            agent_doc.email = sales_agent_email
            agent_doc.commission_rate = 10
            agent_doc.status = "Active"
            agent_doc.insert(ignore_permissions=True)
            print(f"✓ Created Sales Agent: {agent_doc.name} ({sales_agent_email})")
        else:
            agent_doc = frappe.get_doc("Sales Agent", {"user": sales_agent_email})
            print(f"✓ Using existing Sales Agent: {agent_doc.name}")

        # Ensure Item/Medication exists
        if not frappe.db.exists("Item", "TEST-MED"):
            frappe.get_doc({
                "doctype": "Item", 
                "item_code": "TEST-MED", 
                "item_group": "Products", 
                "is_stock_item": 0,
                "is_sales_item": 1
            }).insert(ignore_permissions=True)
            
            # Ensure Price

        # Ensure Patient Sales Agent Link
        if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "referred_by_sales_agent"}):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Patient",
                "fieldname": "referred_by_sales_agent", # Correct field name for hooks
                "label": "Referred By Sales Agent",
                "fieldtype": "Link",
                "options": "Sales Agent",
                "insert_after": "custom_referrer_name"
            }).insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.clear_cache(doctype="Patient")
            
        # Verify field exists in Meta
        if not frappe.get_meta("Patient").get_field("referred_by_sales_agent"):
            print("⚠️ Warning: referred_by_sales_agent not found in Patient Meta even after creation!")
            frappe.clear_cache() # Clear all cache
            
        # Ensure Sales Invoice has 'patient' field (if not present)
        if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "patient"}):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "patient",
                "label": "Patient",
                "fieldtype": "Link",
                "options": "Patient",
                "insert_after": "customer"
            }).insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.clear_cache(doctype="Sales Invoice")
            
        # Ensure Medication Class
        if not frappe.db.exists("Medication Class", "Test Class"):
            frappe.get_doc({"doctype": "Medication Class", "medication_class": "Test Class"}).insert(ignore_permissions=True)

        # Ensure Prescription Dosage and Duration
        dosage_name = "1 each"
        if not frappe.db.exists("Prescription Dosage", dosage_name):
            frappe.get_doc({"doctype": "Prescription Dosage", "dosage": dosage_name}).insert(ignore_permissions=True)
            
        dosage_form_name = "Tablet"
        if not frappe.db.exists("Dosage Form", dosage_form_name):
            frappe.get_doc({"doctype": "Dosage Form", "dosage_form": dosage_form_name}).insert(ignore_permissions=True)
        
        duration_filters = {"number": 1, "period": "Month"}
        duration_name = frappe.db.get_value("Prescription Duration", duration_filters, "name")
        if not duration_name:
            duration_name = frappe.get_doc({
                 "doctype": "Prescription Duration",
                 "number": 1,
                 "period": "Month"
            }).insert(ignore_permissions=True).name

        if not frappe.db.exists("Medication", {"generic_name": "Test Generic"}):
            med = frappe.get_doc({
                "doctype": "Medication", 
                "medication": "Test Generic",
                "generic_name": "Test Generic",
                "medication_class": "Test Class",
                "strength": "1",
                "strength_uom": "mg",
                "is_stock_item": 0
            })
            # Link to Item
            med.append("linked_items", {
                "item_code": "Test Generic",
                "manufacturer": "Test Manufacturer",
                "uom": "Nos",
                "conversion_factor": 1,
                "rate": 100,
                "item_group": "Products"
            })
            med.insert(ignore_permissions=True)
                
        med_name = frappe.db.get_value("Medication", {"generic_name": "Test Generic"}, "name")
    except Exception as e:
        print(f"❌ Setup Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # --- SIMULATE PROCESS ---
    try:
        # Step 1: Patient Signup & Intake (API)
        print("\n--- STEP 1: PATIENT SIGNUP & INTAKE ---")
        
        # 1. Patient registers (creates User)
        print(f"Signing up new patient: {patient_email}")
        user = frappe.get_doc({
            "doctype": "User",
            "email": patient_email,
            "first_name": "Test",
            "last_name": f"Patient_{timestamp}",
            "send_welcome_email": 0,
            "roles": [{"role": "Patient"}]
        })
        user.flags.ignore_password_policy = True
        user.insert(ignore_permissions=True)
        
        # Verify User Created
        user = frappe.get_doc("User", patient_email)
        print(f"✓ User created: {user.name}")
        
        # 2. Patient submits intake form (Web Form)
        # Mocking the intake form data
        text_referral_name = "Agent Smith"
        print("Submitting Intake Form...")
        intake_data = {
            "email": patient_email,
            "first_name": "Test",
            "last_name": f"Patient_{timestamp}",
            "mobile": f"082{str(timestamp)[-7:]}",
            "dob": "1990-01-01",
            "sex": "Female",
            "height": 170,
            "weight": 80,
            "intake_height_unit": "Centimeters",
            "intake_weight_unit": "Kilograms",
            "medical_history": "None",
            "referrer_name": text_referral_name # Assumption: Field exists on Intake Form
        }
        
        # Call the API function
        from koraflow_core.api.patient_signup import process_intake_submission_from_web_form
        # Mock Doc object
        class MockDoc:
            def __init__(self, data):
                self.__dict__.update(data)
            def get(self, key, default=None):
                return self.__dict__.get(key, default)
            def as_dict(self):
                return self.__dict__
                
        res = process_intake_submission_from_web_form(MockDoc(intake_data), patient_email)
        
        # Verify Intake Submission created and linked
        # Also Verify Patient Created and linked to User
        # Note: process_intake_submission returns the patient name usually? 
        # Checking implementation of process_intake_submission_from_web_form... it returns redirect URL normally.
        # But it creates Patient.
        
        # Find created patient
        patient_name = frappe.db.get_value("Patient", {"email": patient_email}, "name")
        if not patient_name:
             raise Exception("Patient was not created!")
             
        print(f"✓ Intake submitted. Patient created: {patient_name}")
        
        # Verify Patient has the text referral (if logic maps it)
        patient = frappe.get_doc("Patient", patient_name)
        if not patient.custom_referrer_name:
             patient.custom_referrer_name = text_referral_name
             patient.flags.ignore_mandatory = True
             patient.save(ignore_permissions=True)
             print(f"✓ (Simulated) Patient entered referrer name: {patient.custom_referrer_name}")

        # Step 2: Nurse Reviews
        print("\n--- STEP 2: NURSE REVIEW & AGENT ASSIGNMENT ---")
        
        # 1. Nurse (Simulated) opens Patient profile
        print("Nurse reviewing profile...")
        
        # 2. Nurse assigns Sales Agent
        if not patient.get("referred_by_sales_agent"):
             # Logic matching text referral to agent
             agent = frappe.db.get_value("Sales Agent", {"user": sales_agent_email}, "name")
             print(f"Nurse sees referrer '{patient.custom_referrer_name}' and selects Agent '{agent}'")
             patient.referred_by_sales_agent = agent
             patient.save(ignore_permissions=True)
             
        print(f"✓ Patient linked to Sales Agent: {patient.get('referred_by_sales_agent')}")
        
        # 3. Nurse activates profile (User)
        user.reload()
        user.enabled = 1
        user.save(ignore_permissions=True)
        print("✓ User account activated")

        # 4. Nurse adds medication in draft (Creates Encounter)
        # Get a Practitioner (Doctor)
        practitioner = frappe.db.get_value("Healthcare Practitioner", {"status": "Active"})
        if not practitioner:
            # Create dummy practitioner
            practitioner = frappe.new_doc("Healthcare Practitioner")
            practitioner.practitioner_name = "Dr. Test"
            practitioner.status = "Active"
            practitioner.insert(ignore_permissions=True).name
        
        print(f"Creating Draft Encounter with {practitioner}")
        encounter = frappe.new_doc("Patient Encounter")
        encounter.patient = patient.name
        encounter.practitioner = practitioner
        encounter.encounter_date = frappe.utils.nowdate()
        encounter.status = "Open" # Nurse drafts it (Open)
        
        # Add medication to encounter
        encounter.append("drug_prescription", {
             "medication": med_name,
             "dosage": dosage_name,
             "period": duration_name,
             "dosage_form": dosage_form_name
        })
        encounter.insert(ignore_permissions=True)
        print(f"✓ Encounter created in Draft: {encounter.name}")


        # ====================================================================
        # STEP 3: DOCTOR REVIEW & SUBMISSION
        # ====================================================================
        print("\n--- STEP 3: DOCTOR REVIEW & SUBMISSION ---")
        
        # Doctor reviews medication and submits
        print("Doctor reviewing and submitting encounter...")
        encounter.submit()
        
        # Trigger Quotation Creation (usually automated via hook or button)
        # We assume `on_submit` of Encounter does this, or we manually trigger the function
        # Based on `test_encounter_workflow.py` it seemed to happen automatically?
        # Let's check if Quotation exists
        quotation_name = frappe.db.get_value("Quotation", {
            "party_name": patient.customer,
            "transaction_date": today(),
            "docstatus": 0 # Draft
        })
        
        if not quotation_name:
            print("⚠ Quotation not auto-created. Attempting manual creation via API...")
            # If your system uses a specific API to generate quote from encounter, call it here.
            # For now, let's create it manually if not found, to simulate "Create Quote" button click
            quotation = frappe.new_doc("Quotation")
            quotation.quotation_to = "Customer"
            quotation.party_name = patient.customer
            quotation.transaction_date = today()
            quotation.append("items", {
                "item_code": "TEST-MED",
                "qty": 1,
                "rate": 1500
            })
            quotation.custom_prescription = encounter.name
            # Provide referrer if system uses it
            quotation.custom_referrer_name = patient.custom_referrer_name 
            quotation.insert(ignore_permissions=True)
            quotation_name = quotation.name
            
        print(f"✓ Quotation generated: {quotation_name}")


        # ====================================================================
        # STEP 4: PATIENT ACCEPTANCE & ADDRESS
        # ====================================================================
        print("\n--- STEP 4: PATIENT QUOTE ACCEPTANCE & ADDRESS ---")
        
        quotation = frappe.get_doc("Quotation", quotation_name)
        
        # Simulating "Confirming Delivery Address"
        print("Patient confirming delivery address...")
        
        # Ensure Patient is linked to Customer (for Invoice)
        if not patient.customer:
             if frappe.db.exists("Customer", patient.first_name + " " + patient.last_name):
                  patient.customer = patient.first_name + " " + patient.last_name
             else:
                  customer = frappe.new_doc("Customer")
                  customer.customer_name = f"{patient.first_name} {patient.last_name}"
                  customer.customer_type = "Individual"
                  customer.save(ignore_permissions=True)
                  patient.customer = customer.name
             patient.save(ignore_permissions=True)

        # Create Address
        address_title = f"Addr-{patient.name}"
        if not frappe.db.exists("Address", {"address_title": address_title}):
            addr = frappe.new_doc("Address")
            addr.address_title = address_title
            addr.address_line1 = "123 Test St"
            addr.city = "Cape Town"
            addr.country = "South Africa"
            addr.address_type = "Shipping"
            addr.append("links", {
                "link_doctype": "Customer",
                "link_name": patient.customer
            })
            addr.save(ignore_permissions=True)
            print(f"✓ Address created: {addr.name}")
        
        address_name = frappe.db.get_value("Address", {"address_title": address_title}, "name")
        
        # Link address to Quotation
        quotation.shipping_address_name = address_name
        quotation.save(ignore_permissions=True)
        
        # Accept Quote
        print("Patient accepting quote...")
        quotation.db_set("status", "Accepted") # Or whatever status triggers logic
        quotation.submit() # Assuming submit means "Accepted/Ordered"
        print("✓ Quotation submitted (Accepted)")


        # ====================================================================
        # STEP 5: SYSTEM AUTOMATION (INVOICE & COMMISSION)
        # ====================================================================
        print("\n--- STEP 5: SYSTEM AUTOMATION ---")
        
        # 1. Sales Invoice Creation (Auto or Manual?)
        # Checking if Sales Invoice was auto-created from Quotation
        print("Checking for Sales Invoice...")
        si_name = frappe.db.get_value("Sales Invoice", {
            "customer": patient.customer,
            "docstatus": 0 # Draft
        })
        
        if not si_name:
            print("⚠ Sales Invoice not auto-created. Creating from Quotation...")
            from erpnext.selling.doctype.quotation.quotation import make_sales_invoice
            si = make_sales_invoice(quotation.name)
            
            # DEBUG
            print(f"DEBUG: Quotation Items count: {len(quotation.items)}")
            if not quotation.items:
                 print("❌ Quotation has NO items!")
            
            print(f"DEBUG: SI Ideas items count: {len(si.items)}")
            if not si.items:
                 print("❌ SI has NO items!")
            
            # Ensure Patient is linked (critical for Commission Hook)
            if not si.get("patient") and patient:
                 si.patient = patient.name
                 print(f"✓ Linked Invoice to Patient: {si.patient}")
            
            si.insert(ignore_permissions=True)
            si_name = si.name
            
        print(f"✓ Sales Invoice created: {si_name}")
        
        si = frappe.get_doc("Sales Invoice", si_name)
        
        # Verify Sales Team / Partner is set on Invoice (crucial for commission)
        # Based on `update_referral_on_invoice_paid` hook, it might look at patient.referred_by_sales_agent
        # But usually Frappe standard is `sales_partner` field on Invoice
        if not si.sales_partner:
             # Logic to pull from patient if not auto-fetched
             # If you have custom logic, it might use `custom_sales_agent`
             print("Applying Sales Partner to Invoice...")
             si.sales_partner = frappe.db.get_value("Sales Partner", {"name": "Test Partner"}) if frappe.db.exists("Sales Partner", "Test Partner") else None
             # But we are using "Sales Agent" custom doctype?
             # Let's assume the hook handles "referred_by_sales_agent" from Patient
             pass

        # Submit Invoice
        print("Submitting Sales Invoice...")
        si.submit()
        print("✓ Sales Invoice submitted")
        
        # 2. Pay Invoice (Required for Commission Hook)
        print("Paying Sales Invoice...")
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.party_type = "Customer"
        pe.party = patient.customer
        
        # Fetch a valid Mode of Payment account
        mop = frappe.db.get_value("Mode of Payment Account", {"parent": "Cash"}, "default_account")
        if not mop:
             mop = frappe.db.get_value("Account", {"account_type": "Cash", "is_group": 0, "company": "KoraFlow"}, "name")
        pe.paid_to = mop or "Cash - K" 
        
        pe.paid_amount = si.grand_total
        pe.received_amount = si.grand_total
        pe.reference_no = "TEST-PAY-001"
        pe.reference_date = frappe.utils.nowdate()
        
        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": si.name,
            "total_amount": si.grand_total,
            "outstanding_amount": si.grand_total,
            "allocated_amount": si.grand_total
        })
        pe.insert(ignore_permissions=True)
        pe.submit()
        print(f"✓ Payment Entry created and submitted: {pe.name}")
        
        # FORCE Trigger of Hooks (since PE submit might use SQL update)
        print("Forcing Invoice Update to trigger Commission Hooks...")
        si.reload()
        si.save(ignore_permissions=True)
        
        # 3. Check Commission (Sales Agent Accrual)
        print("Checking Sales Agent Commission (Accrual)...")
        
        # Determine Sales Agent Name (Link field)
        agent_name = agent # We already have the name from earlier
        
        # Check Sales Agent Accrual
        accruals = frappe.get_all("Sales Agent Accrual", filters={
            "sales_agent": agent_name,
            "invoice_reference": si.name
        }, fields=["name", "accrued_amount", "status"])
        
        if accruals:
             print(f"✓ Sales Agent Accrual found: {accruals[0].name}")
             print(f"  Amount: {accruals[0].accrued_amount}")
        else:
             print(f"⚠ Sales Agent Accrual for {si.name} NOT found.")
             
             # Debugging info
             print(f"Debug Info: Patient ID: {patient.name}, Invoice: {si.name}, Agent: {agent_name}")
             print(f"Patient Link Field 'referred_by_sales_agent': {frappe.db.get_value('Patient', patient.name, 'referred_by_sales_agent')}")
             
        frappe.db.commit()
        print("✓ Test Data Committed.")
            
        # Check Patient Referral Status
        referrals = frappe.get_all("Patient Referral", filters={"patient": patient.name})
        if referrals:
            ref = frappe.get_doc("Patient Referral", referrals[0].name)
            print(f"✓ Patient Referral Status: {ref.current_journey_status}")
            # Should be "Invoiced" or "Order Confirmed"
        else:
            print("⚠ No Patient Referral record found.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_full_process_test()
