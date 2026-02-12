"""
Master Automation Hooks
Prescription → Quotation → Dispense → Courier → Xero

This module handles all automation triggers while preserving SAHPRA/SAPC legal gates:
- Doctor approval = HUMAN GATE #1
- Patient quote acceptance = HUMAN GATE #2  
- Pharmacist dispense = HUMAN GATE #3
"""

import frappe
from frappe import _
from frappe.utils import nowdate


# ====================
# PRESCRIPTION HOOKS
# ====================

def validate_prescription(doc, method):
    """Validate prescription before save"""
    # Ensure quantity within limits (90-day supply max)
    if doc.quantity and doc.quantity > 90:
        frappe.throw(_("Quantity cannot exceed 90-day supply"))


def on_prescription_status_change(doc, method):
    """Handle prescription status changes - triggers quotation generation"""
    if doc.status == "Doctor Approved" and not doc.linked_quotation:
        # Enqueue quotation creation
        frappe.enqueue(
            "koraflow_core.jobs.create_quotation_job",
            prescription_name=doc.name,
            queue="short"
        )
        # Log to compliance audit
        create_audit_log(
            "Prescription", 
            doc.doctype, 
            doc.name, 
            doc.patient,
            {"medication": doc.medication, "dosage": doc.dosage, "doctor": doc.doctor}
        )


# ====================
# QUOTATION HOOKS
# ====================

def on_quotation_update(doc, method):
    """Handle quotation status changes (patient acceptance)"""
    if doc.status == "Ordered" and hasattr(doc, 'glp1_prescription') and doc.glp1_prescription:
        # Check if sales chain already exists
        existing_so = frappe.db.exists("Sales Order", {"quotation": doc.name})
        if existing_so:
            return
            
        # Enqueue sales chain creation
        frappe.enqueue(
            "koraflow_core.jobs.create_sales_chain_job",
            quotation_name=doc.name,
            queue="short"
        )
        # Update prescription status
        frappe.db.set_value("GLP-1 Patient Prescription", 
                          doc.glp1_prescription, "status", "Quoted")
        # Log acceptance
        create_audit_log(
            "Quote Accepted", 
            doc.doctype, 
            doc.name,
            get_patient_from_quotation(doc),
            {"total": doc.grand_total}
        )


# ====================
# INVOICE HOOKS
# ====================

def on_invoice_submit(doc, method):
    """Create dispense queue task when invoice is submitted"""
    prescription = get_prescription_from_invoice(doc)
    if not prescription:
        return
        
    # Check if dispense task already exists
    existing_task = frappe.db.exists("GLP-1 Pharmacy Dispense Task", {"invoice": doc.name})
    if existing_task:
        return
    
    # Create dispense task
    frappe.enqueue(
        "koraflow_core.jobs.create_dispense_task_job",
        invoice_name=doc.name,
        prescription_name=prescription,
        queue="short"
    )
    # Update prescription status
    frappe.db.set_value("GLP-1 Patient Prescription", prescription, "status", "Dispense Queued")
    # Log
    create_audit_log(
        "Invoice", 
        doc.doctype, 
        doc.name, 
        get_patient_from_invoice(doc),
        {"total": doc.grand_total}
    )


# ====================
# STOCK ENTRY (DISPENSE) HOOKS
# ====================

def validate_dispense_entry(doc, method):
    """Validate dispense stock entry - enforce cold chain, batch, roles"""
    if not is_glp1_dispense(doc):
        return
    
    # 1. Verify pharmacist role
    if not frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Pharmacist"}):
        frappe.throw(_("Only licensed Pharmacists can dispense GLP-1 medications"))
    
    # 2. Verify batch/expiry
    for item in doc.items:
        if not item.batch_no:
            frappe.throw(_("Batch number is mandatory for GLP-1 dispense"))
        batch = frappe.get_doc("Batch", item.batch_no)
        if batch.expiry_date and str(batch.expiry_date) < nowdate():
            frappe.throw(_("Cannot dispense expired batch {0}").format(item.batch_no))
    
    # 3. Verify cold chain (custom field on warehouse)
    pharm_warehouse = get_pharm_warehouse()
    if pharm_warehouse:
        cold_chain_valid = frappe.db.get_value("Warehouse", pharm_warehouse, "custom_cold_chain_valid")
        if cold_chain_valid == 0:
            frappe.throw(_("Cold chain breach detected. Cannot dispense until resolved."))


def on_stock_entry_submit(doc, method):
    """Create shipment and trigger courier when stock entry (dispense) is submitted"""
    if not is_glp1_dispense(doc):
        return
    
    # Create shipment
    frappe.enqueue(
        "koraflow_core.jobs.create_shipment_job",
        stock_entry_name=doc.name,
        queue="short"
    )
    
    # Log dispense
    pharmacist_license = get_pharmacist_license(frappe.session.user)
    patient = doc.custom_patient if hasattr(doc, 'custom_patient') else None
    create_audit_log(
        "Dispense", 
        doc.doctype, 
        doc.name, 
        patient,
        {"pharmacist": frappe.session.user, "license": pharmacist_license}
    )


# ====================
# SHIPMENT HOOKS
# ====================

def on_shipment_update(doc, method):
    """Handle shipment status updates"""
    if not doc.has_value_changed("status"):
        return
        
    if doc.status == "Courier Booked":
        create_audit_log(
            "Shipment", 
            doc.doctype, 
            doc.name, 
            doc.patient,
            {"waybill": doc.waybill_number}
        )
    elif doc.status == "Awaiting Collection":
        create_audit_log(
            "Courier Handover", 
            doc.doctype, 
            doc.name, 
            doc.patient,
            {"waybill": doc.waybill_number, "cold_chain": doc.cold_chain_status}
        )


# ====================
# HELPERS
# ====================

def create_audit_log(event_type, ref_doctype, ref_name, patient, details=None):
    """Create GLP-1 Compliance Audit Log entry"""
    try:
        from koraflow_core.utils.glp1_compliance import create_audit_log as _create
        _create(
            event_type=event_type,
            reference_doctype=ref_doctype,
            reference_name=ref_name,
            patient=patient,
            actor=frappe.session.user,
            details=details or {}
        )
    except Exception as e:
        # Log error but don't fail the main operation
        frappe.log_error(f"Failed to create audit log: {str(e)}", "Automation Audit Log")


def is_glp1_dispense(stock_entry):
    """Check if stock entry is a GLP-1 dispense"""
    if stock_entry.purpose != "Material Issue":
        return False
    pharm_warehouse = get_pharm_warehouse()
    if not pharm_warehouse:
        return False
    for item in stock_entry.items:
        if item.s_warehouse == pharm_warehouse:
            return True
    return False


def get_pharm_warehouse():
    """Get PHARM-CENTRAL-COLD warehouse"""
    return frappe.db.get_value(
        "Pharmacy Warehouse",
        {"warehouse_name": "PHARM-CENTRAL-COLD"},
        "erpnext_warehouse"
    )


def get_pharmacist_license(user):
    """Get pharmacist license number"""
    practitioner = frappe.db.get_value("Healthcare Practitioner", {"user_id": user}, "name")
    if practitioner:
        return frappe.db.get_value("Healthcare Practitioner", practitioner, "registration_number")
    return None


def get_patient_from_quotation(doc):
    """Get patient from quotation"""
    if hasattr(doc, 'custom_prescription') and doc.custom_prescription:
        return frappe.db.get_value("GLP-1 Patient Prescription", doc.custom_prescription, "patient")
    return None


def get_patient_from_invoice(doc):
    """Get patient from invoice"""
    customer = doc.customer
    return frappe.db.get_value("Patient", {"customer": customer}, "name")


def get_prescription_from_invoice(doc):
    """Get prescription linked to invoice"""
    # 1. Check direct link
    if hasattr(doc, 'custom_prescription') and doc.custom_prescription:
        return doc.custom_prescription
        
    # 2. Trace via Sales Order Items (custom_prescription on SO or Item)
    if doc.items:
        for item in doc.items:
            # Check item link
            if hasattr(item, 'custom_prescription') and item.custom_prescription:
                return item.custom_prescription
                
            # Check linked Sales Order
            if item.sales_order:
                so_prescription = frappe.db.get_value("Sales Order", item.sales_order, "custom_prescription")
                if so_prescription:
                    return so_prescription

    return None
