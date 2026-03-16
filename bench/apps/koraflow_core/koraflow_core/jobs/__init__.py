# Copyright (c) 2026, KoraFlow Team and Contributors
# License: MIT. See LICENSE

from .xero_jobs import *
"""
Background Jobs for Master Automation Workflow
Prescription → Quotation → Dispense → Courier → Xero

All jobs run asynchronously via frappe.enqueue()
"""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


# ====================
# QUOTATION JOB
# ====================

def create_quotation_job(prescription_name):
    """
    Background job: Create quotation from approved prescription.
    
    Triggered by: Prescription.status = "Doctor Approved"
    Creates: Quotation with medication, dispensing fee, courier fee
    """
    try:
        prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
        
        # Get medication item - check linked_items child table first, then fallback to medication name
        medication = frappe.get_doc("Medication", prescription.medication)
        medication_item = None
        
        # Try linked_items child table (Healthcare module's Medication uses this)
        if medication.linked_items and len(medication.linked_items) > 0:
            medication_item = medication.linked_items[0].item_code if hasattr(medication.linked_items[0], 'item_code') else None
        
        # Fallback: try the item field directly
        if not medication_item:
            medication_item = getattr(medication, 'item', None) or getattr(medication, 'item_code', None)
        
        # Final fallback: use medication name as item code
        if not medication_item and frappe.db.exists("Item", prescription.medication):
            medication_item = prescription.medication
        
        if not medication_item:
            frappe.log_error(title="Quotation Job", message=f"No item for medication {prescription.medication}")
            return
            return
        
        # Get customer from patient
        customer = frappe.db.get_value("Patient", prescription.patient, "customer")
        if not customer:
            frappe.log_error(title="Quotation Job", message=f"No customer for patient {prescription.patient}")
            return
        
        # Get pricing
        item_rate = frappe.db.get_value("Item", medication_item, "standard_rate") or 0
        
        # Get dispensing fee (from Healthcare Settings or default)
        dispensing_fee = 50.0
        try:
            dispensing_fee = frappe.db.get_single_value("Healthcare Settings", "dispensing_fee") or 50.0
        except:
            pass
        
        # Build items list
        items = [
            {
                "item_code": medication_item,
                "qty": prescription.quantity,
                "rate": item_rate,
                "description": f"GLP-1 Medication: {prescription.medication}"
            }
        ]
        
        # Add dispensing fee if item exists
        if frappe.db.exists("Item", "DISPENSING-FEE"):
            items.append({
                "item_code": "DISPENSING-FEE",
                "qty": 1,
                "rate": dispensing_fee,
                "description": "Pharmacist Dispensing Fee"
            })
        
        # Add courier fee if available
        courier_fee = get_courier_fee(prescription.patient)
        if courier_fee and frappe.db.exists("Item", "COURIER-FEE"):
            items.append({
                "item_code": "COURIER-FEE",
                "qty": 1,
                "rate": courier_fee,
                "description": "Courier Delivery Fee"
            })
        
        # Create quotation with correct ERPNext fields
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",      # ERPNext uses quotation_to, not party_type
            "party_name": customer,           # ERPNext uses party_name, not party
            "transaction_date": nowdate(),
            "valid_till": add_days(nowdate(), 2),  # 48-hour validity
            "custom_prescription": prescription_name,  # Use correct custom field name
            "items": items
        })
        
        quotation.flags.from_medication_request = True
        quotation.insert(ignore_permissions=True)
        quotation.submit()  # Auto-submit for patient review
        frappe.db.commit()
        
        # Link quotation to prescription
        frappe.db.set_value("GLP-1 Patient Prescription", prescription_name,
                          "linked_quotation", quotation.name)

        # Store TCG rate metadata on quotation
        rate_info = get_courier_rate_info(prescription.patient)
        if rate_info:
            frappe.db.set_value("Quotation", quotation.name, {
                "custom_courier_rate": rate_info.get("courier_fee"),
                "custom_courier_service_level": rate_info.get("service_level_code")
            })

        # Log to compliance
        log_audit("Quotation", "Quotation", quotation.name, prescription.patient,
                 {"total": quotation.grand_total, "prescription": prescription_name})
        
        frappe.logger().info(f"Created quotation {quotation.name} from prescription {prescription_name}")
        return quotation.name
        
    except Exception as e:
        frappe.log_error(title="Quotation Job", message=f"Error creating quotation: {str(e)}")
        raise


def get_courier_fee(patient):
    """Calculate courier fee via TCG rates API, fallback to default"""
    try:
        settings = frappe.get_single("Courier Guy Settings")
        if not settings.enabled:
            return settings.default_rate or 99.00

        from koraflow_core.utils.courier_guy_api import CourierGuyAPI
        api = CourierGuyAPI()
        result = api.get_rates_for_patient(patient)
        return result.get("courier_fee", settings.default_rate or 99.00)
    except Exception as e:
        frappe.log_error(title="Courier Fee Lookup", message=str(e))
        try:
            return frappe.get_single("Courier Guy Settings").default_rate or 99.00
        except Exception:
            return 99.00


def get_courier_rate_info(patient):
    """Get full courier rate info (fee + service level) for storing on quotation"""
    try:
        settings = frappe.get_single("Courier Guy Settings")
        if not settings.enabled:
            return None

        from koraflow_core.utils.courier_guy_api import CourierGuyAPI
        api = CourierGuyAPI()
        result = api.get_rates_for_patient(patient)

        if result.get("success") and result.get("selected_rate"):
            return {
                "courier_fee": result.get("courier_fee", 0),
                "service_level_code": result.get("service_level_code", ""),
                "service_level_name": result.get("service_level_name", ""),
                "raw_response": result.get("raw_response", {})
            }
        return None
    except Exception as e:
        frappe.log_error(title="Courier Rate Info", message=str(e))
        return None


# ====================
# SALES CHAIN JOB
# ====================

def create_sales_chain_job(quotation_name):
    """
    Background job: Create SO → Picking List → SI from accepted quotation.
    
    Triggered by: Quotation.status = "Ordered" (patient accepted)
    Creates: Sales Order, Pick List, Sales Invoice
    Note: Delivery Note NOT submitted - waits for pharmacist dispense
    """
    try:
        from erpnext.selling.doctype.quotation.quotation import make_sales_order
        from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
        
        quotation = frappe.get_doc("Quotation", quotation_name)
        
        # Create Sales Order
        sales_order = make_sales_order(quotation_name)
        sales_order.flags.from_medication_request = True
        sales_order.delivery_date = add_days(nowdate(), 3)  # 3-day delivery
        
        # Set warehouse for stock items (required for submission)
        default_warehouse = get_pharm_warehouse()
        for item in sales_order.items:
            if not item.warehouse:
                item.warehouse = default_warehouse
        
        # Copy delivery notes
        if hasattr(quotation, 'custom_delivery_notes'):
            sales_order.custom_delivery_notes = quotation.custom_delivery_notes
        
        sales_order.insert(ignore_permissions=True)
        sales_order.submit()
        frappe.db.commit()
        
        # Log Sales Order
        patient = get_patient_from_quotation(quotation)
        log_audit("Sales Order", "Sales Order", sales_order.name, patient,
                 {"quotation": quotation_name})
        
        # Create Picking List
        create_picking_list(sales_order.name, patient)
        
        # Create Sales Invoice (this triggers dispense task)
        sales_invoice = make_sales_invoice(sales_order.name)
        sales_invoice.flags.from_medication_request = True
        
        # Set custom fields
        if hasattr(sales_order, 'custom_prescription') and sales_order.custom_prescription:
            if hasattr(sales_invoice, 'custom_prescription'):
                sales_invoice.custom_prescription = sales_order.custom_prescription
        
        if hasattr(sales_order, 'custom_delivery_notes'):
            sales_invoice.custom_delivery_notes = sales_order.custom_delivery_notes
                
        sales_invoice.insert(ignore_permissions=True)
        sales_invoice.submit()
        frappe.db.commit()
        
        frappe.logger().info(f"Created sales chain from quotation {quotation_name}: SO={sales_order.name}, SI={sales_invoice.name}")
        return sales_invoice.name
        
    except Exception as e:
        frappe.log_error(title="Sales Chain Job", message=f"Error creating sales chain: {str(e)}")
        raise


def create_picking_list(sales_order_name, patient=None):
    """Create picking list from sales order"""
    try:
        so = frappe.get_doc("Sales Order", sales_order_name)
        
        pick_list = frappe.new_doc("Pick List")
        pick_list.company = so.company
        pick_list.purpose = "Delivery"
        pick_list.customer = so.customer
        
        # Add items
        for item in so.items:
            pick_list.append("locations", {
                "item_code": item.item_code,
                "qty": item.qty,
                "stock_qty": item.stock_qty,
                "warehouse": item.warehouse,
                "sales_order": sales_order_name,
                "sales_order_item": item.name,
                "uom": item.uom,
                "conversion_factor": item.conversion_factor or 1
            })
            
        # Add GLP-1 context fields via custom fields
        if hasattr(so, 'custom_prescription') and so.custom_prescription:
            if hasattr(pick_list, 'custom_glp1_prescription'):
                pick_list.custom_glp1_prescription = so.custom_prescription
            if hasattr(pick_list, 'custom_patient'):
                pick_list.custom_patient = patient or so.customer_name # Fallback
        
        pick_list.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Log
        log_audit("Picking", "Pick List", pick_list.name, patient,
                 {"sales_order": sales_order_name})
        
        frappe.logger().info(f"Created picking list {pick_list.name} from SO {sales_order_name}")
        return pick_list.name
        
    except Exception as e:
        frappe.log_error(title="Picking List Job", message=f"Error creating picking list: {str(e)}")
        return None


# ====================
# DISPENSE TASK JOB
# ====================

def create_dispense_task_job(invoice_name, prescription_name):
    """
    Background job: Create pharmacy dispense task.
    
    Triggered by: Sales Invoice submitted
    Creates: GLP-1 Pharmacy Dispense Task in "Pending" status
    """
    try:
        prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
        
        # Check if task already exists
        existing = frappe.db.exists("GLP-1 Pharmacy Dispense Task", 
                                   {"prescription": prescription_name, "status": ["!=", "Dispensed"]})
        if existing:
            frappe.logger().info(f"Dispense task already exists for prescription {prescription_name}")
            return existing
        
        task = frappe.get_doc({
            "doctype": "GLP-1 Pharmacy Dispense Task",
            "patient": prescription.patient,
            "prescription": prescription_name,
            "invoice": invoice_name,
            "status": "Pending"
        })
        task.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger().info(f"Created dispense task {task.name} for prescription {prescription_name}")
        return task.name
        
    except Exception as e:
        frappe.log_error(title="Dispense Task Job", message=f"Error creating dispense task: {str(e)}")
        raise


# ====================
# SHIPMENT JOB
# ====================

def create_shipment_job(stock_entry_name):
    """
    Background job: Create shipment and trigger Courier Guy API.
    
    Triggered by: Stock Entry (Material Issue from PHARM-CENTRAL-COLD) submitted
    Creates: GLP-1 Shipment, calls Courier Guy API, attaches waybill
    """
    try:
        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Get patient and prescription
        patient = stock_entry.custom_patient if hasattr(stock_entry, 'custom_patient') else None
        prescription = None
        
        if patient:
            prescription = frappe.db.get_value(
                "GLP-1 Patient Prescription",
                {"patient": patient, "status": "Dispense Queued"},
                "name",
                order_by="creation desc"
            )
        
        if not prescription:
            frappe.log_error(title="Shipment Job", message=f"No prescription found for stock entry {stock_entry_name}")
            return None
        
        # Create shipment
        shipment = frappe.get_doc({
            "doctype": "GLP-1 Shipment",
            "prescription": prescription,
            "patient": patient,
            "stock_entry": stock_entry_name,
            "status": "Created",
            "cold_chain_status": "Valid",
            "delivery_note": getattr(stock_entry, 'custom_delivery_notes', None)
        })
        shipment.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Update prescription status
        frappe.db.set_value("GLP-1 Patient Prescription", prescription, "status", "Shipped")
        
        # Trigger Courier Guy API (async)
        frappe.enqueue(
            "koraflow_core.jobs.book_courier_job",
            shipment_name=shipment.name,
            queue="short"
        )
        
        frappe.logger().info(f"Created shipment {shipment.name} from stock entry {stock_entry_name}")
        return shipment.name
        
    except Exception as e:
        frappe.log_error(title="Shipment Job", message=f"Error creating shipment: {str(e)}")
        raise


def book_courier_job(shipment_name):
    """
    Background job: Book courier and attach waybill.
    
    Triggered by: Shipment created
    Calls: Courier Guy API, updates shipment with waybill
    """
    try:
        from koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill import create_waybill_from_shipment
        
        shipment = frappe.get_doc("GLP-1 Shipment", shipment_name)
        
        # Get patient address for delivery
        patient = frappe.get_doc("Patient", shipment.patient) if shipment.patient else None
        if not patient:
            frappe.log_error(title="Courier Booking", message=f"No patient found for shipment {shipment_name}")
            return
        
        # Call Courier Guy API to create waybill
        try:
            waybill_doc = create_waybill_from_shipment(shipment_name)
            
            if waybill_doc:
                # Update shipment with waybill details
                shipment.waybill = waybill_doc.name
                shipment.waybill_number = waybill_doc.waybill_number if hasattr(waybill_doc, 'waybill_number') else None
                shipment.courier_reference = waybill_doc.shiplogic_id if hasattr(waybill_doc, 'shiplogic_id') else None
                shipment.status = "Awaiting Collection"
                shipment.save()
                frappe.db.commit()
                
                # Log
                log_audit("Waybill", "GLP-1 Shipment", shipment_name, shipment.patient,
                         {"waybill": shipment.waybill_number})
                
                frappe.logger().info(f"Courier booked for shipment {shipment_name}: waybill={shipment.waybill_number}")
                
        except Exception as courier_error:
            # Log courier error but don't fail the shipment
            frappe.log_error(title="Courier Booking", message=f"Courier API error for shipment {shipment_name}: {str(courier_error)}")
            shipment.status = "Created"  # Retry later
            shipment.cold_chain_notes = f"Courier booking failed: {str(courier_error)}"
            shipment.save()
            frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(title="Courier Booking", message=f"Error booking courier: {str(e)}")
        raise


# ====================
# XERO SYNC JOBS
# ====================

def sync_xero_after_invoice(invoice_name):
    """
    Background job: Sync invoice to Xero after submission.
    """
    try:
        from koraflow_core.utils.xero_connector import sync_invoice
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        sync_invoice(doc)
    except Exception as e:
        frappe.log_error(title="Xero Sync", message=f"Error syncing invoice to Xero: {str(e)}")


# ====================
# CLEANUP JOBS
# ====================

def cleanup_expired_quotes():
    """
    Scheduled job: Mark expired quotes as cancelled.
    Runs daily via scheduler.
    """
    try:
        expired_quotes = frappe.get_all(
            "Quotation",
            filters={
                "status": ["in", ["Draft", "Open"]],
                "valid_till": ["<", nowdate()],
                "glp1_prescription": ["is", "set"]
            },
            pluck="name"
        )
        
        for quote_name in expired_quotes:
            frappe.db.set_value("Quotation", quote_name, "status", "Expired")
            
            # Also update linked prescription
            prescription = frappe.db.get_value("Quotation", quote_name, "glp1_prescription")
            if prescription:
                frappe.db.set_value("GLP-1 Patient Prescription", prescription, 
                                  "linked_quotation", None)
        
        frappe.db.commit()
        frappe.logger().info(f"Cleaned up {len(expired_quotes)} expired GLP-1 quotes")
        
    except Exception as e:
        frappe.log_error(title="Quote Cleanup", message=f"Error cleaning up expired quotes: {str(e)}")


# ====================
# HELPERS
# ====================

def log_audit(event_type, ref_doctype, ref_name, patient, details=None):
    """Create compliance audit log entry"""
    try:
        from koraflow_core.utils.glp1_compliance import create_audit_log
        create_audit_log(
            event_type=event_type,
            reference_doctype=ref_doctype,
            reference_name=ref_name,
            patient=patient,
            actor=frappe.session.user,
            details=details or {}
        )
    except Exception as e:
        frappe.log_error(title="Jobs Audit Log", message=f"Failed to create audit log: {str(e)}")


def get_patient_from_quotation(doc):
    """Get patient from quotation"""
    if hasattr(doc, 'glp1_prescription') and doc.glp1_prescription:
        return frappe.db.get_value("GLP-1 Patient Prescription", doc.glp1_prescription, "patient")
    return None


def get_pharm_warehouse():
    """Get the default pharmacy warehouse"""
    return "PHARM-CENTRAL-COLD - S2W"  # Default cold chain warehouse
