import frappe
from frappe import _

def notify_doctor_of_draft(doc, method):
    """Notify the assigned practitioner when a nurse saves a draft encounter."""
    
    # Only fire when saved as draft
    if doc.docstatus != 0:
        return
    
    # We only trigger this if the person making the change has the Nurse role
    if "Nurse" not in frappe.get_roles(frappe.session.user):
        return
        
    if not doc.practitioner:
        return

    # Get doctor's user account
    doctor_user = frappe.db.get_value(
        "Healthcare Practitioner", doc.practitioner, "user"
    )
    
    if not doctor_user:
        return

    frappe.sendmail(
        recipients=[doctor_user],
        subject=f"Patient Encounter Ready for Review — {doc.patient_name}",
        message=f"""
            <p>A draft Patient Encounter has been saved by a nurse and is ready for your review.</p>
            <ul>
                <li><strong>Patient:</strong> {doc.patient_name}</li>
                <li><strong>Date:</strong> {doc.encounter_date}</li>
                <li><strong>Saved by:</strong> {frappe.session.user}</li>
            </ul>
            <p>
                <a href="/app/patient-encounter/{doc.name}">
                    Click here to review and submit
                </a>
            </p>
        """,
        now=True
    )
