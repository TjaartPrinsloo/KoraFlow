"""
End-to-End Workflow Test for Patient Eben
Tests the complete flow from nurse review to dispatch
"""

import frappe
from frappe.utils import nowdate, add_days

def run_test():
    frappe.init(site="koraflow-site")
    frappe.connect()
    
    try:
        print("=" * 60)
        print("END-TO-END WORKFLOW TEST FOR PATIENT EBEN")
        print("=" * 60)
        
        # Step 1: Find patient Eben
        print("\n📋 Step 1: Finding patient Eben...")
        eben = frappe.get_doc("Patient", "Eben")
        print(f"  ✅ Found patient: {eben.patient_name}")
        print(f"     Email: {eben.email}")
        print(f"     Status: {eben.status}")
        print(f"     Customer: {eben.customer}")
        
        # Enable patient if disabled
        if eben.status == "Disabled":
            print("  ⚠️ Patient is disabled, enabling...")
            eben.status = "Active"
            eben.save(ignore_permissions=True)
            frappe.db.commit()
            print("  ✅ Patient enabled")
        
        # Ensure customer exists
        if not eben.customer:
            print("  ⚠️ No customer linked, creating...")
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": eben.patient_name,
                "customer_type": "Individual",
                "customer_group": "Individual"
            })
            customer.insert(ignore_permissions=True)
            eben.customer = customer.name
            eben.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"  ✅ Created customer: {customer.name}")
        
        # Step 2: Create or find intake submission
        print("\n📋 Step 2: Checking intake submission...")
        existing_submission = frappe.db.exists("GLP-1 Intake Submission", {"first_name": "Eben"})
        
        if existing_submission:
            print(f"  ✅ Found existing submission: {existing_submission}")
            submission = frappe.get_doc("GLP-1 Intake Submission", existing_submission)
        else:
            print("  ⚠️ No submission found, creating test submission...")
            submission = frappe.get_doc({
                "doctype": "GLP-1 Intake Submission",
                "first_name": "Eben",
                "last_name": "TestPatient",
                "email": eben.email,
                "sex": "Male",
                "intake_height_cm": 175,
                "intake_weight_kg": 85,
                "intake_bp_systolic": 120,
                "intake_bp_diastolic": 80,
                "intake_heart_rate": 72
            })
            submission.insert(ignore_permissions=True)
            submission.submit()
            frappe.db.commit()
            print(f"  ✅ Created submission: {submission.name}")
        
        # Step 3: Create intake review (Nurse Review)
        print("\n👩‍⚕️ Step 3: Nurse Review...")
        existing_review = frappe.db.exists("GLP-1 Intake Review", {"intake_submission": submission.name})
        
        if existing_review:
            review = frappe.get_doc("GLP-1 Intake Review", existing_review)
            print(f"  ✅ Found existing review: {review.name} (Status: {review.status})")
        else:
            review = frappe.get_doc({
                "doctype": "GLP-1 Intake Review",
                "intake_submission": submission.name,
                "status": "Pending"
            })
            review.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  ✅ Created review: {review.name}")
        
        # Approve the review
        if review.status != "Approved":
            print("  📝 Approving intake review...")
            review.status = "Approved"
            review.save(ignore_permissions=True)
            frappe.db.commit()
            print("  ✅ Review approved by nurse")
        
        # Step 4: Create prescription (Doctor's role)
        print("\n👨‍⚕️ Step 4: Doctor Prescription...")
        
        # Check for available medications
        medications = frappe.get_all("Medication", fields=["name"], limit=1)
        if not medications:
            print("  ⚠️ No medications found, creating test medication...")
            # Check if item exists
            if not frappe.db.exists("Item", "GLP1-SEMAGLUTIDE"):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": "GLP1-SEMAGLUTIDE",
                    "item_name": "Semaglutide 0.5mg",
                    "item_group": "Products",
                    "stock_uom": "Unit",
                    "is_stock_item": 1,
                    "standard_rate": 1500
                })
                item.insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"    ✅ Created item: {item.item_code}")
            
            medication_name = "Semaglutide"
        else:
            medication_name = medications[0].name
            print(f"  ✅ Using medication: {medication_name}")
        
        # Create prescription
        prescription = frappe.get_doc({
            "doctype": "GLP-1 Patient Prescription",
            "patient": eben.name,
            "medication": medication_name,
            "dosage": "0.5mg weekly",
            "quantity": 4,
            "status": "Draft"
        })
        prescription.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  ✅ Created prescription: {prescription.name}")
        
        # Doctor approves prescription (this should trigger quotation)
        print("  📝 Doctor approving prescription...")
        prescription.status = "Doctor Approved"
        prescription.save(ignore_permissions=True)
        frappe.db.commit()
        print("  ✅ Prescription approved by doctor")
        
        # Step 5: Check/Create Quotation
        print("\n💰 Step 5: Quotation Generation...")
        frappe.db.commit()  # Ensure hooks are committed
        
        # Check if quotation was auto-created
        quotation = None
        if prescription.linked_quotation:
            quotation = frappe.get_doc("Quotation", prescription.linked_quotation)
            print(f"  ✅ Quotation auto-generated: {quotation.name}")
        else:
            print("  ⚠️ No auto-quotation found, creating manually...")
            # Get medication item
            item_code = frappe.db.get_value("Medication", medication_name, "item") or "GLP1-SEMAGLUTIDE"
            
            quotation = frappe.get_doc({
                "doctype": "Quotation",
                "quotation_to": "Customer",
                "party_name": eben.customer,
                "transaction_date": nowdate(),
                "valid_till": add_days(nowdate(), 30),
                "custom_prescription": prescription.name,
                "items": [{
                    "item_code": item_code if frappe.db.exists("Item", item_code) else "GLP1-SEMAGLUTIDE",
                    "qty": prescription.quantity,
                    "rate": 1500
                }]
            })
            quotation.insert(ignore_permissions=True)
            quotation.submit()
            frappe.db.commit()
            
            # Link to prescription
            prescription.linked_quotation = quotation.name
            prescription.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"  ✅ Created quotation: {quotation.name}")
        
        print(f"     Total: {quotation.grand_total}")
        
        # Step 6: Patient accepts quote
        print("\n✅ Step 6: Patient Quote Acceptance...")
        if quotation.status != "Ordered":
            quotation.status = "Ordered"
            quotation.save(ignore_permissions=True)
            frappe.db.commit()
            print("  ✅ Quote accepted by patient")
        else:
            print("  ✅ Quote already accepted")
        
        # Check if sales order was created
        sales_orders = frappe.get_all("Sales Order", filters={"quotation": quotation.name}, limit=1)
        if sales_orders:
            print(f"  ✅ Sales Order auto-created: {sales_orders[0].name}")
        else:
            print("  ⚠️ Sales Order not auto-created (may need manual trigger)")
        
        # Step 7: Check for dispense task
        print("\n💊 Step 7: Pharmacy Dispense Task...")
        dispense_tasks = frappe.get_all("GLP-1 Pharmacy Dispense Task", 
                                         filters={"patient": eben.name},
                                         fields=["name", "status"])
        if dispense_tasks:
            print(f"  ✅ Dispense task found: {dispense_tasks[0].name} (Status: {dispense_tasks[0].status})")
        else:
            print("  ⚠️ No dispense task found (may require Sales Invoice)")
        
        # Step 8: Summary
        print("\n" + "=" * 60)
        print("WORKFLOW TEST SUMMARY")
        print("=" * 60)
        print(f"  Patient: {eben.patient_name}")
        print(f"  Intake Submission: {submission.name}")
        print(f"  Intake Review: {review.name} (Status: {review.status})")
        print(f"  Prescription: {prescription.name} (Status: {prescription.status})")
        print(f"  Quotation: {quotation.name} (Status: {quotation.status})")
        
        # List all created documents
        print("\n📄 Documents created in this test:")
        print(f"  - GLP-1 Intake Submission: {submission.name}")
        print(f"  - GLP-1 Intake Review: {review.name}")
        print(f"  - GLP-1 Patient Prescription: {prescription.name}")
        print(f"  - Quotation: {quotation.name}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        frappe.destroy()

if __name__ == "__main__":
    run_test()
