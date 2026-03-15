import frappe
from koraflow_core.api.patient_signup import create_patient_from_intake
from koraflow_core.utils.patient_sync import sync_intake_to_patient

def verify():
    frappe.errprint("Starting Medication Sync Verification...")
    
    # 1. Prepare test data
    test_email = "test_medication_sync@example.com"
    
    # Delete existing test patient if any
    if frappe.db.exists("Patient", {"email": test_email}):
        frappe.delete_doc("Patient", frappe.db.get_value("Patient", {"email": test_email}, "name"), force=True)
        frappe.db.commit()
    
    intake_data = {
        "email": test_email,
        "first_name": "Test",
        "last_name": "MedSyncUnique",
        "mobile": "0998877665",
        "dob": "1990-01-01",
        "sex": "Male",
        "intake_height_cm": 180,
        "intake_height_unit": "Centimeters",
        "intake_weight_kg": 80,
        "intake_weight_unit": "Kilograms",
        "medications": [
            {
                "medication": "Metformin",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "status": "Current"
            },
            {
                "medication": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "status": "Stopped",
                "stopped_date": "2024-02-01",
                "reason_for_stopping": "Dry cough"
            }
        ]
    }

    # 2. Create patient and intake submission
    frappe.errprint(f"Creating patient from intake for {test_email}...")
    result = create_patient_from_intake(intake_data, user_email=test_email)
    
    if not result.get("success"):
        frappe.errprint(f"FAILED: {result.get('message')}")
        return

    patient_name = result.get("patient")
    frappe.errprint(f"Patient created: {patient_name}")

    # 3. Verify GLP-1 Intake Submission
    patient = frappe.get_doc("Patient", patient_name)
    frappe.errprint(f"Patient glp1_intake_forms count: {len(patient.glp1_intake_forms)}")
    
    latest_intake_row = patient.glp1_intake_forms[-1]
    frappe.errprint(f"Latest intake row name: {latest_intake_row.name}")
    
    # Check if medications are in the row object directly first
    frappe.errprint(f"Medications in intake row (memory): {len(latest_intake_row.medications or [])}")

    latest_intake = frappe.get_doc("GLP-1 Intake Submission", latest_intake_row.name)
    frappe.errprint(f"Verifying Intake Submission {latest_intake.name} from DB...")
    frappe.errprint(f"Medications in Intake Submission (DB): {len(latest_intake.medications or [])}")
    
    # 5. Verify Patient Custom Field (reload doc to see automatic sync result)
    frappe.errprint("Verifying Patient medication history (automatic sync)...")
    patient = frappe.get_doc("Patient", patient_name)
    frappe.errprint(f"Medications in history: {len(patient.custom_medication_history or [])}")
    frappe.errprint(f"Medications in history: {len(patient.custom_medication_history or [])}")
    
    if len(patient.custom_medication_history or []) == 2:
        frappe.errprint("VERIFICATION SUCCESSFUL!")
    else:
        frappe.errprint("VERIFICATION FAILED: Medication counts mismatch")

    return

if __name__ == "__main__":
    frappe.connect()
    try:
        verify()
    finally:
        frappe.destroy()
