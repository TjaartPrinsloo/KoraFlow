"""
Xero Webhook Processing Jobs

Handles incoming Xero webhook events for:
- Invoice status updates (Paid, Voided)
- Payment created notifications
- Credit note processing
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def xero_webhook():
    """
    Webhook endpoint for Xero status updates.
    Called when invoice is paid, voided, or credit note issued.

    Configure in Xero Developer Portal:
    - URL: https://portal.slim2well.com/api/method/koraflow_core.jobs.xero_jobs.xero_webhook
    - Events: INVOICE.UPDATED, PAYMENT.CREATED
    """
    import json

    if not frappe.request.data:
        return {"status": "error", "message": "No payload received"}

    try:
        payload = json.loads(frappe.request.data)
    except json.JSONDecodeError:
        frappe.log_error(title="Xero Webhook", message="Invalid JSON in Xero webhook")
        return {"status": "error", "message": "Invalid JSON"}

    # Xero sends validation requests - respond immediately
    if payload.get("firstEventSequence") == 0:
        return {"status": "ok"}

    events = payload.get("events", [])

    for event in events:
        event_type = event.get("eventType")
        resource_id = event.get("resourceId")
        tenant_id = event.get("tenantId")

        if event_type == "INVOICE.UPDATED":
            frappe.enqueue(
                "koraflow_core.jobs.xero_jobs.process_xero_invoice_update",
                xero_invoice_id=resource_id,
                tenant_id=tenant_id,
                queue="short"
            )
        elif event_type == "PAYMENT.CREATED":
            frappe.enqueue(
                "koraflow_core.jobs.xero_jobs.process_xero_payment_created",
                payment_id=resource_id,
                tenant_id=tenant_id,
                queue="short"
            )

    return {"status": "ok", "processed": len(events)}


def process_xero_invoice_update(xero_invoice_id, tenant_id=None):
    """
    Process Xero invoice status update.

    Triggered by: Xero webhook INVOICE.UPDATED
    Actions:
    - Fetch invoice from Xero
    - If Paid: Create Payment Entry in Frappe (triggers waybill chain)
    - If Voided: Mark invoice as voided
    """
    try:
        from koraflow_core.utils.xero_connector import get_xero_connector

        connector = get_xero_connector()
        api = connector.get_accounting_api()

        tenant = tenant_id or connector.settings.tenant_id

        try:
            xero_invoice = api.get_invoice(tenant, xero_invoice_id)
        except Exception as api_error:
            frappe.log_error(title="Xero Invoice Error",
                message=f"Error fetching Xero invoice {xero_invoice_id}: {str(api_error)}")
            return

        if not xero_invoice or not xero_invoice.invoices:
            return

        invoice = xero_invoice.invoices[0]

        # Find matching Frappe invoice by Xero ID
        frappe_invoice = frappe.db.get_value(
            "Sales Invoice",
            {"custom_xero_invoice_id": xero_invoice_id},
            "name"
        )

        if not frappe_invoice and invoice.invoice_number:
            # Try by invoice number (Frappe SI name)
            if frappe.db.exists("Sales Invoice", invoice.invoice_number):
                frappe_invoice = invoice.invoice_number
            else:
                frappe_invoice = frappe.db.get_value(
                    "Sales Invoice",
                    {"custom_xero_invoice_number": invoice.invoice_number},
                    "name"
                )

        if not frappe_invoice:
            frappe.log_error(title="Xero Webhook",
                message=f"No matching Frappe invoice for Xero {xero_invoice_id}")
            return

        # Update Xero status on the Frappe invoice
        frappe.db.set_value("Sales Invoice", frappe_invoice,
            "custom_xero_status", invoice.status)

        if invoice.status == "PAID":
            handle_xero_payment(frappe_invoice, invoice)
        elif invoice.status == "VOIDED":
            handle_xero_void(frappe_invoice)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(title="Xero Webhook",
            message=f"Error processing Xero webhook: {str(e)}")


def process_xero_payment_created(payment_id, tenant_id=None):
    """Process Xero payment created event."""
    try:
        from koraflow_core.utils.xero_connector import get_xero_connector

        connector = get_xero_connector()
        api = connector.get_accounting_api()
        tenant = tenant_id or connector.settings.tenant_id

        try:
            xero_payment = api.get_payment(tenant, payment_id)
        except Exception as api_error:
            frappe.log_error(title="Xero Payment Error",
                message=f"Error fetching Xero payment {payment_id}: {str(api_error)}")
            return

        if not xero_payment or not xero_payment.payments:
            return

        payment = xero_payment.payments[0]

        if payment.invoice and payment.invoice.invoice_id:
            process_xero_invoice_update(payment.invoice.invoice_id, tenant_id)

    except Exception as e:
        frappe.log_error(title="Xero Webhook",
            message=f"Error processing Xero payment webhook: {str(e)}")


def handle_xero_payment(frappe_invoice_name, xero_invoice):
    """Handle Xero payment notification - create Payment Entry in Frappe.
    This triggers the existing payment chain: PE submit → waybill booking → commission.
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", frappe_invoice_name)

        if invoice.status == "Paid" or invoice.outstanding_amount <= 0:
            return

        # Dedupe: check if a Xero-sourced Payment Entry already exists
        xero_ref = f"XERO-{xero_invoice.invoice_id[:8]}" if xero_invoice.invoice_id else "XERO"
        existing_pe = frappe.db.exists("Payment Entry", {
            "reference_no": xero_ref,
            "docstatus": ["!=", 2]
        })
        if existing_pe:
            return

        # Create payment entry using ERPNext helper
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

        payment = get_payment_entry("Sales Invoice", frappe_invoice_name)
        payment.paid_amount = invoice.outstanding_amount
        payment.received_amount = invoice.outstanding_amount
        payment.reference_no = xero_ref
        payment.reference_date = xero_invoice.fully_paid_on_date or frappe.utils.nowdate()

        payment.insert(ignore_permissions=True)
        payment.submit()
        frappe.db.commit()

        # Update Xero status
        frappe.db.set_value("Sales Invoice", frappe_invoice_name, "custom_xero_status", "PAID")

        # Audit logging (resilient - won't break payment chain if audit module missing)
        try:
            patient = get_patient_from_invoice(invoice)
            log_audit("Payment", "Payment Entry", payment.name, patient,
                     {"amount": payment.paid_amount, "source": "Xero", "xero_id": xero_invoice.invoice_id})
            log_audit("Xero Sync", "Sales Invoice", frappe_invoice_name, patient,
                     {"status": "Paid", "xero_id": xero_invoice.invoice_id})
        except Exception:
            pass  # Don't let audit failures break payment processing

        frappe.logger().info(f"Created payment {payment.name} from Xero for invoice {frappe_invoice_name}")

    except Exception as e:
        frappe.log_error(title="Xero Payment",
            message=f"Error handling Xero payment for {frappe_invoice_name}: {str(e)}")


def handle_xero_void(frappe_invoice_name):
    """Handle Xero void notification."""
    try:
        frappe.db.set_value("Sales Invoice", frappe_invoice_name, {
            "custom_xero_voided": 1,
            "custom_xero_status": "VOIDED"
        })
        frappe.db.commit()

        try:
            invoice = frappe.get_doc("Sales Invoice", frappe_invoice_name)
            patient = get_patient_from_invoice(invoice)
            log_audit("Xero Sync", "Sales Invoice", frappe_invoice_name, patient,
                     {"status": "Voided"})
        except Exception:
            pass

        frappe.logger().info(f"Invoice {frappe_invoice_name} marked as voided from Xero")

    except Exception as e:
        frappe.log_error(title="Xero Void",
            message=f"Error handling Xero void: {str(e)}")


def poll_xero_statuses():
    """Fallback polling for Xero status updates. Runs hourly via scheduler."""
    try:
        from koraflow_core.utils.xero_connector import get_xero_connector

        connector = get_xero_connector()
        connector.sync_xero_payments()

    except Exception as e:
        frappe.log_error(title="Xero Poll",
            message=f"Error polling Xero statuses: {str(e)}")


# ====================
# HELPERS
# ====================

def get_patient_from_invoice(doc):
    """Get patient from invoice customer."""
    return frappe.db.get_value("Patient", {"customer": doc.customer}, "name")


def log_audit(event_type, ref_doctype, ref_name, patient, details=None):
    """Create compliance audit log entry (resilient - errors are silently caught)."""
    try:
        from koraflow_core.utils.glp1_compliance import create_audit_log
        create_audit_log(
            event_type=event_type,
            reference_doctype=ref_doctype,
            reference_name=ref_name,
            patient=patient,
            actor=frappe.session.user if frappe.session.user else "System",
            details=details or {}
        )
    except Exception as e:
        frappe.log_error(title="Xero Jobs Audit Log",
            message=f"Failed to create audit log: {str(e)}")
