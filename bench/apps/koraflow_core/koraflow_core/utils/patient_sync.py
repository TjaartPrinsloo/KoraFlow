import frappe
from frappe import _

def update_patient_uid(doc, method):
    """
    Syncs the ID Number from GLP-1 Intake Form to the linked Patient's UID field.
    This ensures that the Patient record always reflects the latest verified ID from the intake.
    """
    if not doc.pk:
        # Document not yet saved? Should not happen on on_update but good to check
        return

    # 1. Start with the ID Number from the form
    id_number = doc.id_number
    if not id_number:
        # If no ID provided, nothing to sync
        return

    # 2. Find the Patient linked to the current User (doc.owner)
    # The Intake Form is created by the Patient User.
    user = doc.owner
    if not user:
        return

    # Find patient where user_id matches or email matches
    patient_name = frappe.db.get_value("Patient", {"user_id": user}, "name")
    
    if not patient_name:
        # Fallback: Check if email matches (common initial setup)
        patient_name = frappe.db.get_value("Patient", {"email": user}, "name")

    if not patient_name:
        # If still no patient found, we can't sync
        return

    # 3. Update the Patient UID if different
    patient_uid = frappe.db.get_value("Patient", patient_name, "uid")
    
    if patient_uid != id_number:
        try:
            frappe.db.set_value("Patient", patient_name, "uid", id_number)
            frappe.msgprint(_("Patient ID Number updated from Intake Form."))
        except frappe.UniqueValidationError:
            # If ID is already taken by ANOTHER patient, this will fail.
            # We should warn the user but not block the form submission? 
            # OR block it? Patient uniqueness is critical.
            # Let's block it with a clear message.
            frappe.throw(_("The ID Number {0} is already linked to another Patient record. Please verify your ID.").format(id_number))
