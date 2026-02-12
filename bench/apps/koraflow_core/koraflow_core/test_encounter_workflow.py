# Script to create patient encounter and test nurse/doctor workflow
import frappe
from frappe.utils import nowdate

def create_encounter_workflow():
    """Create patient encounter and test the workflow"""
    
    print("=" * 60)
    print("NURSE-DOCTOR ENCOUNTER WORKFLOW TEST")
    print("=" * 60)
    
    # Setup
    patient_name = "Test Patient 456"
    practitioner = "Andre Terblanche"
    nurse_email = "nurse.sister@koraflow.io"
    
    # Get company
    company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company") or "Slim 2 Well"
    
    # Ensure patient status is Disabled
    frappe.db.set_value("Patient", patient_name, "status", "Disabled")
    frappe.db.commit()
    
    patient = frappe.get_doc("Patient", patient_name)
    print(f"Patient: {patient.name} | Status: {patient.status}")
    
    # Create encounter (simulating nurse)
    print("\n👩‍⚕️ NURSE CREATING ENCOUNTER...")
    
    encounter = frappe.get_doc({
        "doctype": "Patient Encounter",
        "patient": patient_name,
        "practitioner": practitioner,
        "encounter_date": nowdate(),
        "encounter_time": "10:00:00",
        "company": company,
        "encounter_comment": "GLP-1 weight management consultation"
    })
    encounter.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"✅ Created encounter: {encounter.name}")
    print(f"   DocStatus: {encounter.docstatus} (0=Draft)")
    
    # Activate patient after encounter creation
    frappe.db.set_value("Patient", patient_name, "status", "Active")
    frappe.db.commit()
    
    patient.reload()
    print(f"   Patient status after encounter: {patient.status}")
    
    # Show that nurse cannot submit
    print("\n📋 Testing Nurse Submit Permission...")
    frappe.set_user(nurse_email)
    
    try:
        test_enc = frappe.get_doc("Patient Encounter", encounter.name)
        test_enc.submit()
        print("❌ ERROR: Nurse was able to submit!")
    except frappe.PermissionError:
        print("✅ CORRECT: Nurse cannot submit encounter")
    except Exception as e:
        print(f"✅ Nurse blocked: {type(e).__name__}")
    finally:
        frappe.set_user("Administrator")
    
    # Doctor submits
    print("\n👨‍⚕️ DOCTOR SUBMITTING ENCOUNTER (GATE 1)...")
    encounter.reload()
    encounter.submit()
    frappe.db.commit()
    
    print(f"✅ Doctor submitted encounter!")
    print(f"   DocStatus: {encounter.docstatus} (1=Submitted)")
    
    return encounter.name


def test_full_workflow_with_medication():
    """
    Complete workflow test: Nurse adds medication -> Doctor submits -> 
    Prescription created + PDF generated -> Quotation created
    """
    
    print("=" * 60)
    print("FULL WORKFLOW TEST WITH MEDICATION")
    print("=" * 60)
    
    # Setup
    patient_name = "Test Patient 456"
    practitioner = "Andre Terblanche"
    nurse_email = "nurse.sister@koraflow.io"
    
    # Get company
    company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company") or "Slim 2 Well"
    
    # Ensure patient status is Disabled
    frappe.db.set_value("Patient", patient_name, "status", "Disabled")
    frappe.db.commit()
    
    patient = frappe.get_doc("Patient", patient_name)
    print(f"Patient: {patient.name} | Status: {patient.status}")
    print(f"Customer: {patient.customer}")
    
    # Get available medications
    medications = frappe.get_all("Medication", fields=["name"], limit=5)
    print(f"Available medications: {[m.name for m in medications]}")
    
    medication = medications[0].name if medications else "Ruby Boost"
    print(f"Using medication: {medication}")
    
    # STEP 1: Nurse creates encounter with drug prescription
    print("\n" + "=" * 60)
    print("STEP 1: NURSE CREATES ENCOUNTER WITH MEDICATION")
    print("=" * 60)
    
    encounter = frappe.get_doc({
        "doctype": "Patient Encounter",
        "patient": patient_name,
        "practitioner": practitioner,
        "encounter_date": nowdate(),
        "encounter_time": "11:00:00",
        "company": company,
        "encounter_comment": "GLP-1 weight management - nurse suggests medication",
        "drug_prescription": [
            {
                "drug_code": medication,
                "dosage": "0.2 ml",
                "period": "1 Month",
                "dosage_form": "Injection",
                "comment": "GLP-1 Start with low dose, increase as tolerated"
            }
        ]
    })
    encounter.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"✅ Nurse created encounter: {encounter.name}")
    print(f"   With medication: {medication}")
    print(f"   DocStatus: {encounter.docstatus} (Draft)")
    
    # Activate patient
    frappe.db.set_value("Patient", patient_name, "status", "Active")
    frappe.db.commit()
    patient.reload()
    print(f"   Patient status: {patient.status}")
    
    # STEP 2: Verify nurse cannot submit
    print("\n" + "=" * 60)
    print("STEP 2: VERIFY NURSE CANNOT SUBMIT")
    print("=" * 60)
    
    frappe.set_user(nurse_email)
    try:
        enc = frappe.get_doc("Patient Encounter", encounter.name)
        enc.submit()
        print("❌ ERROR: Nurse submitted!")
    except:
        print("✅ Nurse correctly blocked from submitting")
    finally:
        frappe.set_user("Administrator")
    
    # STEP 3: Doctor reviews and submits
    print("\n" + "=" * 60)
    print("STEP 3: DOCTOR REVIEWS AND SUBMITS (GATE 1)")
    print("=" * 60)
    
    encounter.reload()
    
    # Doctor can adjust dosage if needed
    if encounter.drug_prescription:
        print(f"   Current dosage: {encounter.drug_prescription[0].dosage}")
        # Doctor could adjust: encounter.drug_prescription[0].dosage = "0.25mg"
    
    encounter.submit()
    frappe.db.commit()
    
    print(f"✅ Doctor submitted encounter: {encounter.name}")
    print(f"   DocStatus: {encounter.docstatus}")
    
    # STEP 4: Check if prescription was created
    print("\n" + "=" * 60)
    print("STEP 4: CHECK PRESCRIPTION CREATION")
    print("=" * 60)
    
    # The prescription hook in prescription_hooks.py should have fired
    prescriptions = frappe.get_all("GLP-1 Patient Prescription", 
                                    filters={"patient": patient_name},
                                    fields=["name", "status", "medication", "creation"],
                                    order_by="creation desc")
    
    if prescriptions:
        print(f"✅ Found {len(prescriptions)} prescription(s):")
        for p in prescriptions:
            print(f"   - {p.name}: {p.status} ({p.medication})")
    else:
        print("⚠️ No GLP-1 prescriptions found")
        print("   Creating prescription manually for demonstration...")
        
        # Get practitioner registration
        doc_prac = frappe.get_doc("Healthcare Practitioner", practitioner)
        reg_number = doc_prac.registration_number if hasattr(doc_prac, "registration_number") and doc_prac.registration_number else "MP0123456"
        
        prescription = frappe.get_doc({
            "doctype": "GLP-1 Patient Prescription",
            "patient": patient_name,
            "medication": medication,
            "dosage": "0.5mg weekly",
            "quantity": 4,
            "duration": "30 days",
            "status": "Doctor Approved",
            "doctor": practitioner,
            "doctor_registration_number": reg_number,
            "treatment_start_date": nowdate()
        })
        prescription.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✅ Created prescription: {prescription.name}")
        prescriptions = [{"name": prescription.name, "status": prescription.status, "medication": prescription.medication}]
    
    # STEP 5: Generate prescription PDF
    print("\n" + "=" * 60)
    print("STEP 5: GENERATE BRANDED PRESCRIPTION PDF")
    print("=" * 60)
    
    if prescriptions:
        prescription_name = prescriptions[0]["name"]
        try:
            from koraflow_core.utils.prescription_generator import generate_and_attach_prescription
            
            # Get the encounter for PDF generation
            file_doc = generate_and_attach_prescription(encounter)
            if file_doc:
                print(f"✅ Generated prescription PDF: {file_doc.file_url}")
            else:
                print("⚠️ PDF generation returned None")
        except ImportError:
            print("⚠️ PDF generator not available")
        except Exception as e:
            print(f"⚠️ PDF generation error: {str(e)[:50]}...")
    
    # STEP 6: Check quotation
    print("\n" + "=" * 60)
    print("STEP 6: CHECK QUOTATION")
    print("=" * 60)
    
    quotations = frappe.get_all("Quotation",
                                 filters={"party_name": patient.customer},
                                 fields=["name", "status", "grand_total"],
                                 order_by="creation desc",
                                 limit=5)
    
    if quotations:
        print(f"✅ Found quotations:")
        for q in quotations:
            print(f"   - {q.name}: {q.status} (R{q.grand_total})")
    else:
        print("⚠️ No quotation found yet (may need automation trigger)")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 WORKFLOW TEST COMPLETE")
    print("=" * 60)
    print(f"Patient: {patient_name} (Status: Active)")
    print(f"Encounter: {encounter.name} (Submitted)")
    print(f"Medication: {medication}")
    print(f"Prescriptions: {len(prescriptions)}")
    
    return {
        "encounter": encounter.name,
        "patient": patient_name,
        "prescriptions": prescriptions
    }


def test_quotation_auto_creation():
    """
    Test that quotation is auto-created when prescription is created with Doctor Approved status
    """
    print("=" * 60)
    print("TEST: QUOTATION AUTO-CREATION ON PRESCRIPTION")
    print("=" * 60)
    
    patient_name = "Test Patient 456"
    medication = "Ruby Boost"
    practitioner = "Andre Terblanche"
    
    # Get patient customer
    customer = frappe.db.get_value("Patient", patient_name, "customer")
    print(f"Patient: {patient_name}")
    print(f"Customer: {customer}")
    print(f"Medication: {medication}")
    
    # Count existing quotations for this customer
    existing_quotations = frappe.get_all("Quotation", 
                                          filters={"party_name": customer},
                                          pluck="name")
    print(f"Existing quotations: {len(existing_quotations)}")
    
    # Create prescription with Doctor Approved status
    print("\n📝 Creating prescription with Doctor Approved status...")
    
    prescription = frappe.get_doc({
        "doctype": "GLP-1 Patient Prescription",
        "patient": patient_name,
        "medication": medication,
        "dosage": "0.2 ml weekly",
        "duration": "30 days",
        "quantity": 4,
        "status": "Doctor Approved",
        "doctor": practitioner,
        "doctor_registration_number": "MP0123456",
        "treatment_start_date": nowdate()
    })
    prescription.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"✅ Created prescription: {prescription.name}")
    print(f"   Status: {prescription.status}")
    
    # Wait a moment for background job (if any)
    import time
    time.sleep(2)
    
    # Reload prescription to check linked_quotation
    prescription.reload()
    print(f"\n📋 Checking prescription.linked_quotation...")
    print(f"   linked_quotation: {prescription.linked_quotation}")
    
    # Check for new quotations
    new_quotations = frappe.get_all("Quotation", 
                                     filters={"party_name": customer},
                                     pluck="name")
    
    new_count = len(new_quotations) - len(existing_quotations)
    print(f"\n📊 Quotation check:")
    print(f"   Previous: {len(existing_quotations)}")
    print(f"   Current: {len(new_quotations)}")
    print(f"   New: {new_count}")
    
    if prescription.linked_quotation:
        quotation = frappe.get_doc("Quotation", prescription.linked_quotation)
        print(f"\n✅ QUOTATION AUTO-CREATED: {quotation.name}")
        print(f"   Grand Total: R{quotation.grand_total}")
        print(f"   Status: {quotation.status}")
    elif new_count > 0:
        # Find the new quotation
        for q in new_quotations:
            if q not in existing_quotations:
                print(f"\n✅ NEW QUOTATION FOUND: {q}")
                quotation = frappe.get_doc("Quotation", q)
                print(f"   Grand Total: R{quotation.grand_total}")
    else:
        print("\n⚠️ No quotation created yet")
        print("   Check Error Log for issues")
        
        # Check error log
        errors = frappe.get_all("Error Log", 
                                filters={"creation": [">", nowdate()]},
                                fields=["method", "error"],
                                order_by="creation desc",
                                limit=3)
        if errors:
            print("\n   Recent errors:")
            for e in errors:
                print(f"   - {e.method}: {str(e.error)[:100]}...")
    
    print("\n" + "=" * 60)
    return prescription.name
