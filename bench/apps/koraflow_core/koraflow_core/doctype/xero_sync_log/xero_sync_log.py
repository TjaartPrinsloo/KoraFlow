import frappe
from frappe.model.document import Document


class XeroSyncLog(Document):
    pass


def create_sync_log(sync_type, direction, reference_doctype=None, reference_name=None,
                    xero_id=None, status="Success", error_message=None):
    """Create a Xero Sync Log entry."""
    try:
        log = frappe.new_doc("Xero Sync Log")
        log.sync_type = sync_type
        log.direction = direction
        log.reference_doctype = reference_doctype
        log.reference_name = reference_name
        log.xero_id = xero_id
        log.status = status
        log.error_message = error_message
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit()
        return log.name
    except Exception as e:
        frappe.log_error(title="Xero Sync Log",
            message=f"Failed to create sync log: {str(e)}")
