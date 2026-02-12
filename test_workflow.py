#!/usr/bin/env python3
"""
End-to-End Workflow Test Script
Creates test data and verifies automation flow from patient signup to dispensing
"""

import frappe
from frappe.utils import now, add_days


def test_complete_workflow():
    """Test the complete automation workflow"""
    
    print("=" * 80)
    print("KORAFLOW AUTOMATION WORKFLOW TEST")
    print("=" * 80)
    
    # Step 1: Find or create test patient
    print("\n[1] Finding test patient...")
    patient_email = "test.patient.new.456@example.com"
    
    patient = frappe.db.get_value("Patient", {"email": patient_email}, ["name", "patient_name"], as_dict=True)
    
    if not patient:
        print(f"❌ Patient with email {patient_email} not found!")
        print("   Please run the patient signup flow first.")
        return
    
    print(f"✅ Found patient: {patient.name} ({patient.patient_name})")
    
    # Step 2: Find a practitioner
    print("\n[2] Finding a practitioner...")
    practitioner = frappe.db.get_value("Healthcare Practitioner", {}, ["name", "practitioner_name"], as_dict=True)
    
    if not practitioner:
        print("❌ No practitioners found! Creating one...")
        prac_doc = frappe.get_doc({
            "doctype": "Healthcare Practitioner",
            "first_name": "Dr. Test",
            "last_name": "Doctor",
            "practitioner_name": "Dr. Test Doctor",
            "department": "General Medicine"
        })
        prac_doc.insert(ignore_permissions=True)
        practitioner = {"name": prac_doc.name, "practitioner_name": prac_doc.practitioner_name}
        print(f"✅ Created practitioner: {practitioner['name']}")
    else:
        print(f"✅ Found practitioner: {practitioner['name']} ({practitioner['practitioner_name']})")
    
    # Step 3: Find a GLP-1 medication
    print("\n[3] Finding medication...")
    medication = frappe.db.get_value(
        "Item",
        {"item_group": "Medicines", "disabled": 0},
        ["name", "item_name", "stock_uom"],
        as_dict=True
    )
    
    if not medication:
        print("❌ No medications found!")
        return
    
    print(f"✅ Found medication: {medication['name']} ({medication['item_name']})")

    
    # Step 4: Create Patient Encounter with Prescription
    print("\n[4] Creating Patient Encounter with prescription...")
    
    encounter = frappe.get_doc({
        "doctype": "Patient Encounter",
        "patient": patient.name,
        "practitioner": practitioner.name,
        "encounter_date": now(),
        "encounter_time": now(),
        "company": frappe.defaults.get_global_default("company"),
        "drug_prescription": [
            {
                "drug_code": medication.name,
                "drug_name": medication.item_name,
                "dosage": "1 injection",
                "period": "Weekly",
                "dosage_form": "Injection",
                "interval": "1 Week",
                "interval_uom": "Week"
            }
        ]
    })
    
    encounter.insert(ignore_permissions=True)
    print(f"✅ Created encounter: {encounter.name}")
    
    # Step 5: Submit the encounter (should trigger prescription generation)
    print("\n[5] Submitting encounter (should generate prescription PDF)...")
    try:
        encounter.submit()
        print(f"✅ Encounter submitted successfully")
        
        # Check if prescription was created
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Patient Encounter", "attached_to_name": encounter.name},
            fields=["name", "file_name"]
        )
        
        if attachments:
            print(f"✅ Prescription PDF generated: {attachments[0]['file_name']}")
        else:
            print("⚠️  No prescription PDF found (might be expected if PDF generation is not configured)")
    
    except Exception as e:
        print(f"❌ Error submitting encounter: {str(e)}")
        return
    
    # Step 6: Check for auto-created Quotation
    print("\n[6] Checking for auto-created Quotation...")
    quotations = frappe.get_all(
        "Quotation",
        filters={"party_name": patient.name},
        fields=["name", "status", "grand_total"],
        order_by="creation desc",
        limit=1
    )
    
    if quotations:
        print(f"✅ Quotation created: {quotations[0]['name']} (Status: {quotations[0]['status']}, Total: {quotations[0]['grand_total']})")
    else:
        print("❌ No quotation found - automation may not be configured")
        print("   Please check: koraflow_core/hooks/healthcare_dispensing_hooks.py")
    
    # Step 7: Check for Sales Order
    print("\n[7] Checking for auto-created Sales Order...")
    sales_orders = frappe.get_all(
        "Sales Order",
        filters={"customer": patient.name},
        fields=["name", "status", "grand_total"],
        order_by="creation desc",
        limit=1
    )
    
    if sales_orders:
        print(f"✅ Sales Order created: {sales_orders[0]['name']} (Status: {sales_orders[0]['status']}, Total: {sales_orders[0]['grand_total']})")
    else:
        print("⚠️  No Sales Order found - may need manual conversion from Quotation")
    
    # Step 8: Check for Pick List
    print("\n[8] Checking for Pick List...")
    pick_lists = frappe.get_all(
        "Pick List",
        filters={},
        fields=["name", "purpose", "docstatus"],
        order_by="creation desc",
        limit=1
    )
    
    if pick_lists:
        print(f"✅ Pick List found: {pick_lists[0]['name']} (Status: {pick_lists[0]['docstatus']})")
    else:
        print("⚠️  No Pick List found - may need to be created from Sales Order")
    
    # Step 9: Check for Commission Records
    print("\n[9] Checking for Commission Records...")
    commissions = frappe.get_all(
        "Commission Record",
        filters={"patient": patient.name},
        fields=["name", "commission_status", "commission_amount"],
        order_by="creation desc",
        limit=1
    )
    
    if commissions:
        print(f"✅ Commission Record created: {commissions[0]['name']} (Status: {commissions[0]['commission_status']}, Amount: {commissions[0]['commission_amount']})")
    else:
        print("⚠️  No Commission Record found - may be created later in the workflow")
    
    print("\n" + "=" * 80)
    print("WORKFLOW TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print(f"  Patient: {patient.name}")
    print(f"  Encounter: {encounter.name}")
    print(f"  Quotations: {len(quotations)}")
    print(f"  Sales Orders: {len(sales_orders)}")
    print(f"  Pick Lists: {len(pick_lists)}")
    print(f"  Commissions: {len(commissions)}")


if __name__ == "__main__":
    frappe.init(site="koraflow-site")
    frappe.connect()
    test_complete_workflow()
    frappe.db.commit()
