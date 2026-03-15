# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1DispenseConfirmation(Document):
	def validate(self):
		"""Validate dispense confirmation"""
		if not self.patient_acknowledgment:
			frappe.throw(_("Patient acknowledgment is required"))
		
		# Verify stock entry exists and is submitted
		if self.stock_entry:
			stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
			if stock_entry.docstatus != 1:
				frappe.throw(_("Stock Entry must be submitted before confirmation"))
	
	def on_submit(self):
		"""Update prescription status and create audit log"""
		# Update prescription status
		if self.prescription:
			frappe.db.set_value("GLP-1 Patient Prescription", self.prescription, "status", "Dispensed")
		
		# Create audit log
		from koraflow_core.utils.glp1_compliance import create_audit_log
		create_audit_log(
			event_type="Dispense",
			reference_doctype="GLP-1 Dispense Confirmation",
			reference_name=self.name,
			patient=self.patient,
			actor=self.pharmacist,
			details={
				"batch": self.batch,
				"stock_entry": self.stock_entry,
				"patient_acknowledged": self.patient_acknowledgment
			}
		)
