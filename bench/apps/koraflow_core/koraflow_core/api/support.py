# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _

@frappe.whitelist()
def create_patient_support_ticket(subject, description, category):
    """
    Create a new support ticket (Issue) for the patient.
    Categories: "Clinical", "Pharmacy"
    """
    if not subject or not description:
        frappe.throw(_("Subject and Description are required."))
        
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Please log in to submit a support ticket."), frappe.PermissionError)
        
    # Get patient linked to user
    patient_name = frappe.db.get_value("Patient", {"user_id": user}, "name")
    if not patient_name:
        frappe.throw(_("No patient profile found for this user."))
        
    patient_doc = frappe.get_doc("Patient", patient_name)
    customer = patient_doc.customer
    
    issue_type, full_description = get_issue_type_and_description(category, description)
    
    # Create the Issue
    issue = frappe.get_doc({
        "doctype": "Issue",
        "subject": subject,
        "description": full_description,
        "raised_by": user,
        "customer": customer,
        "custom_patient": patient_name,
        "custom_is_portal_ticket": 1,
        "status": "Open",
        "priority": "Medium",
        "issue_type": issue_type
    })
    
    # Link assigned nurse if exists
    if patient_doc.custom_assigned_nurse:
        # We can use Frappe's Assignment system or just a custom notification
        issue.flags.assigned_nurse = patient_doc.custom_assigned_nurse
        
    issue.insert(ignore_permissions=True)
    
    # Notify Assigned Nurse
    if patient_doc.custom_assigned_nurse:
        notify_assigned_nurse(issue, patient_doc.custom_assigned_nurse)
        
    return {
        "message": _("Your support ticket has been created successfully (Reference: {0}). Our team will get back to you soon.").format(issue.name),
        "issue": issue.name
    }

def get_issue_type_and_description(category, description):
    """Helper to map portal categories to Desk Issue Types and formatted description."""
    issue_type = "Support"
    clinical_categories = ["Side Effects", "Prescriptions"]
    pharmacy_categories = ["Billing/Payments", "Delivery", "Other"]
    
    if category in clinical_categories:
        issue_type = "Clinical Support"
    elif category in pharmacy_categories:
        issue_type = "Pharmacy Support"
        
    if not frappe.db.exists("Issue Type", issue_type):
        issue_type = None
        
    full_description = f"<b>Category:</b> {category}<br><br>{description}"
    return issue_type, full_description

def notify_assigned_nurse(issue, nurse_email):
    """Send a notification to the assigned nurse about the new ticket."""
    try:
        subject = _("New Support Ticket: {0}").format(issue.subject)
        message = _("""
            <p>Hello,</p>
            <p>A new support ticket has been raised by patient <b>{0}</b>.</p>
            <p><b>Subject:</b> {1}</p>
            <p><b>Description:</b><br>{2}</p>
            <p><a href="/app/issue/{3}">Click here to view the ticket in the Desk</a></p>
        """).format(
            frappe.db.get_value("Patient", issue.custom_patient, "patient_name") or issue.custom_patient,
            issue.subject,
            issue.description,
            issue.name
        )
        
        frappe.sendmail(
            recipients=[nurse_email],
            subject=subject,
            message=message,
            reference_doctype="Issue",
            reference_name=issue.name
        )
        
        # Also create a Frappe System Notification if possible
        if frappe.db.exists("DocType", "Notification Log"):
            frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": nurse_email,
                "subject": subject,
                "email_content": message,
                "document_type": "Issue",
                "document_name": issue.name,
                "type": "Mention"
            }).insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(title="Support Ticket Notification", message=f"Error notifying assigned nurse: {str(e)}")

@frappe.whitelist()
def get_support_history():
    """Get support ticket history for the current patient."""
    user = frappe.session.user
    patient_name = frappe.db.get_value("Patient", {"user_id": user}, "name")
    
    if not patient_name:
        return []
        
    issues = frappe.get_all(
        "Issue",
        filters={"custom_patient": patient_name, "custom_is_portal_ticket": 1},
        fields=["name", "subject", "status", "creation", "issue_type"],
        order_by="creation desc",
        limit=10
    )
    
    return issues

@frappe.whitelist()
def get_support_history_for_desk(patient):
    """Get support ticket history for a specific patient in Desk mode."""
    if not frappe.has_permission("Patient", "read", patient):
        return []

    issues = frappe.get_all(
        "Issue",
        filters={"custom_patient": patient},
        fields=["name", "subject", "status", "creation", "issue_type"],
        order_by="creation desc",
        limit=10
    )
    
    return issues

@frappe.whitelist()
def create_patient_support_ticket_from_desk(patient, subject, description, category):
    """
    Create a new support ticket (Issue) for the patient from the Desk view.
    Used by the Patient form dashboard.
    """
    if not frappe.has_permission("Patient", "write", patient):
        frappe.throw(_("No permission to create support tickets for this patient."))
        
    patient_doc = frappe.get_doc("Patient", patient)
    customer = patient_doc.customer
    
    issue_type, full_description = get_issue_type_and_description(category, description)
    
    # Create the Issue
    issue = frappe.get_doc({
        "doctype": "Issue",
        "subject": subject,
        "description": full_description,
        "raised_by": frappe.session.user,
        "customer": customer,
        "custom_patient": patient,
        "custom_is_portal_ticket": 0, # Raised from desk
        "status": "Open",
        "priority": "Medium",
        "issue_type": issue_type
    })
    
    issue.insert(ignore_permissions=True)
    
    return {
        "message": _("Support ticket created successfully."),
        "issue": issue.name
    }
