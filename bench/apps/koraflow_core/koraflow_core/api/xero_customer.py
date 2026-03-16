"""
API endpoints for Xero Customer onboarding.
Allows nurses/admins to create user accounts and send intake forms
for customers imported from Xero.
"""

import frappe
from frappe import _


@frappe.whitelist()
def create_user_for_xero_customer(customer_name):
    """Create a User account and Patient record for a Xero-imported customer.

    Args:
        customer_name: The Customer doctype name

    Returns:
        dict with success status and created user/patient info
    """
    # Permission check
    if not frappe.has_permission("Customer", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    customer = frappe.get_doc("Customer", customer_name)

    if not customer.get("custom_is_xero_customer"):
        frappe.throw(_("This is not a Xero-imported customer"))

    if not customer.email_id:
        frappe.throw(_("Customer must have an email address to create a user account"))

    # Check if user already exists
    if frappe.db.exists("User", customer.email_id):
        frappe.throw(_("User account already exists for {0}").format(customer.email_id))

    # Create User
    user = frappe.new_doc("User")
    user.email = customer.email_id
    user.first_name = customer.customer_name.split(" ")[0] if customer.customer_name else customer.customer_name
    last_name_parts = customer.customer_name.split(" ")[1:] if customer.customer_name else []
    user.last_name = " ".join(last_name_parts) if last_name_parts else ""
    user.send_welcome_email = 1
    user.user_type = "Website User"

    # Add Website User role
    user.append("roles", {"role": "Website User"})

    user.flags.ignore_permissions = True
    user.insert()

    # Create Patient record linked to Customer
    patient = None
    existing_patient = frappe.db.get_value("Patient", {"customer": customer_name}, "name")

    if not existing_patient:
        patient = frappe.new_doc("Patient")
        patient.patient_name = customer.customer_name
        patient.sex = "Male"  # Default, can be updated via intake form
        patient.email = customer.email_id
        patient.mobile = customer.get("mobile_no") or ""
        patient.customer = customer_name

        patient.flags.ignore_permissions = True
        patient.insert()
    else:
        patient = frappe.get_doc("Patient", existing_patient)

    return {
        "success": True,
        "user": user.name,
        "patient": patient.name if patient else existing_patient
    }


@frappe.whitelist()
def send_intake_form(customer_name):
    """Send intake form to a Xero-imported customer.

    Args:
        customer_name: The Customer doctype name

    Returns:
        dict with success status
    """
    if not frappe.has_permission("Customer", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    customer = frappe.get_doc("Customer", customer_name)

    if not customer.email_id:
        frappe.throw(_("Customer must have an email address"))

    # Check if user exists
    if not frappe.db.exists("User", customer.email_id):
        frappe.throw(_("Please create a user account first before sending the intake form"))

    # Check if patient exists
    patient_name = frappe.db.get_value("Patient", {"customer": customer_name}, "name")
    if not patient_name:
        frappe.throw(_("Please create a user account first (this also creates the patient record)"))

    # Send intake form link via email
    intake_url = frappe.utils.get_url("/glp1-intake")

    frappe.sendmail(
        recipients=[customer.email_id],
        subject=_("Please Complete Your Intake Form - Slim2Well"),
        message=_("""
<p>Dear {customer_name},</p>

<p>Welcome to Slim2Well! Before we can proceed with your treatment, we need you to complete your intake form.</p>

<p>Please click the link below to complete your intake form:</p>

<p><a href="{intake_url}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Complete Intake Form</a></p>

<p>If you have any questions, please don't hesitate to contact us.</p>

<p>Kind regards,<br>The Slim2Well Team</p>
""").format(customer_name=customer.customer_name, intake_url=intake_url),
        now=True
    )

    return {"success": True}
