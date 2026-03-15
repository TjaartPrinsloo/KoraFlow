# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, add_days


class GLP1CompoundingRecord(Document):
	def validate(self):
		"""Validate compounding legality per SAHPRA regulations"""
		self.validate_prescription_link()
		self.validate_quantity_limit()
		self.validate_active_ingredient()
	
	def validate_prescription_link(self):
		"""Compounding must reference prescription and patient"""
		if not self.prescription:
			frappe.throw(_("Prescription is mandatory for compounding"))
		if not self.patient:
			frappe.throw(_("Patient is mandatory for compounding"))
		
		# Verify prescription belongs to patient
		prescription = frappe.get_doc("GLP-1 Patient Prescription", self.prescription)
		if prescription.patient != self.patient:
			frappe.throw(_("Prescription patient does not match compounding patient"))
	
	def validate_quantity_limit(self):
		"""Quantity must not exceed prescription limit (max 30 days)"""
		if self.prescription and self.compound_quantity:
			prescription = frappe.get_doc("GLP-1 Patient Prescription", self.prescription)
			if self.compound_quantity > prescription.quantity:
				frappe.throw(_("Compound quantity ({0}) cannot exceed prescription quantity ({1})").format(
					self.compound_quantity, prescription.quantity
				))
			
			# Max 30 days supply for compounding
			if self.compound_quantity > 30:
				frappe.throw(_("Compound quantity cannot exceed 30 days supply per SAHPRA regulations"))
	
	def validate_active_ingredient(self):
		"""Active ingredient must match registered product"""
		# This is a simplified check - adjust based on your Medication/Batch structure
		if self.source_batch:
			batch = frappe.get_doc("Batch", self.source_batch)
			# Verify batch contains registered active ingredient
			# Implementation depends on your batch structure
			pass
	
	def on_submit(self):
		"""Create audit log for compounding"""
		from koraflow_core.utils.glp1_compliance import create_audit_log
		create_audit_log(
			event_type="Compounding",
			reference_doctype="GLP-1 Compounding Record",
			reference_name=self.name,
			patient=self.patient,
			actor=self.responsible_pharmacist,
			actor_license=self.pharmacist_license,
			details={
				"compound_quantity": self.compound_quantity,
				"beyond_use_date": str(self.beyond_use_date),
				"source_batch": self.source_batch
			}
		)
