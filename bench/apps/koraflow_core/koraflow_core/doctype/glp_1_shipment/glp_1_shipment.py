# Copyright (c) 2026, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1Shipment(Document):
    def validate(self):
        """Validate shipment prerequisites"""
        if not self.prescription:
            frappe.throw(_("Prescription is required"))
        if not self.patient:
            frappe.throw(_("Patient is required"))
        
        # Validate cold chain status
        if self.cold_chain_status == "Breach Detected" and self.status not in ["Failed", "Created"]:
            frappe.throw(_("Cannot proceed with shipment when cold chain breach is detected"))
    
    def on_update(self):
        """Handle status updates"""
        if self.has_value_changed("status"):
            self.log_status_change()
            
            # Update prescription status
            if self.prescription:
                if self.status == "Awaiting Collection":
                    frappe.db.set_value("GLP-1 Patient Prescription", self.prescription, "status", "Shipped")
                elif self.status == "Delivered":
                    frappe.db.set_value("GLP-1 Patient Prescription", self.prescription, "status", "Delivered")
    
    def log_status_change(self):
        """Log status change to compliance audit"""
        from koraflow_core.utils.glp1_compliance import create_audit_log
        
        create_audit_log(
            event_type="Shipment",
            reference_doctype=self.doctype,
            reference_name=self.name,
            patient=self.patient,
            actor=frappe.session.user,
            details={
                "status": self.status,
                "waybill": self.waybill_number,
                "cold_chain": self.cold_chain_status
            }
        )


@frappe.whitelist()
def create_shipment_from_dispense(stock_entry_name, prescription_name=None, patient=None):
    """
    Create shipment document from a dispense stock entry.
    Called automatically after pharmacist dispense.
    """
    stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
    
    # Get prescription if not provided
    if not prescription_name and patient:
        prescription_name = frappe.db.get_value(
            "GLP-1 Patient Prescription",
            {"patient": patient, "status": "Dispense Queued"},
            "name",
            order_by="creation desc"
        )
    
    if not prescription_name:
        frappe.log_error(title="Shipment Creation", message=f"No prescription found for stock entry {stock_entry_name}")
        return None
    
    prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
    
    # Create shipment
    shipment = frappe.get_doc({
        "doctype": "GLP-1 Shipment",
        "prescription": prescription_name,
        "patient": prescription.patient,
        "stock_entry": stock_entry_name,
        "status": "Created",
        "cold_chain_status": "Valid"
    })
    
    shipment.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return shipment.name
