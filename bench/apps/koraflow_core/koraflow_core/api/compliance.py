import frappe
from frappe import _

@frappe.whitelist()
def get_personal_data_export(user=None):
    """
    PAIA Compliance: Export all personal data linked to a user.
    """
    if not user:
        user = frappe.session.user

    # Permission Check
    if frappe.session.user != user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Not authorized to export data for this user"), frappe.PermissionError)

    data = {
        "User": frappe.get_doc("User", user).as_dict(),
        "Personal Data": {},
        "Documents": {}
    }

    # 1. Check for Patient Record
    if frappe.db.exists("Patient", {"email": user}):
        patient = frappe.get_doc("Patient", {"email": user})
        data["Personal Data"]["Patient Record"] = patient.as_dict()
        
        # Get linked Encounters
        encounters = frappe.get_all("Patient Encounter", filters={"patient": patient.name}, fields=["*"])
        data["Documents"]["Encounters"] = encounters

        # Get linked Vitals
        vitals = frappe.get_all("Patient Vital", filters={"patient": patient.name}, fields=["*"])
        data["Documents"]["Vitals"] = vitals
        
        # Get Prescriptions
        prescriptions = frappe.get_all("GLP-1 Patient Prescription", filters={"patient": patient.name}, fields=["*"])
        data["Documents"]["Prescriptions"] = prescriptions

    # 2. Check for Sales Agent Record
    if frappe.db.exists("Sales Agent Bank Details", {"sales_agent": user}):
        bank_details = frappe.get_doc("Sales Agent Bank Details", {"sales_agent": user})
        data["Personal Data"]["Bank Details"] = bank_details.as_dict()

    # Log the export for Audit
    frappe.log("Access Log", message=f"PAIA Data Export for user: {user} by {frappe.session.user}")

    return data
