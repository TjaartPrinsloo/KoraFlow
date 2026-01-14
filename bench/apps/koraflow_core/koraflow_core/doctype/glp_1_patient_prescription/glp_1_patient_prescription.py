# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1PatientPrescription(Document):
	def validate(self):
		"""Validate prescription data"""
		self.validate_doctor_license()
		self.validate_medication_schedule()
		self.validate_quantity_limits()
	
	def before_submit(self):
		"""Set status to Doctor Approved on submit"""
		if self.status == "Draft":
			self.status = "Doctor Approved"
		self.validate_immutable_fields()
	
	def on_submit(self):
		"""Create audit log and trigger workflow"""
		from koraflow_core.utils.glp1_compliance import create_audit_log
		create_audit_log(
			event_type="Prescription",
			reference_doctype="GLP-1 Patient Prescription",
			reference_name=self.name,
			patient=self.patient,
			actor=frappe.session.user,
			details={"status": self.status, "medication": self.medication}
		)
	
	def validate_doctor_license(self):
		"""Validate doctor is licensed"""
		if not self.doctor_registration_number:
			frappe.throw(_("Doctor Registration Number is required"))
		
		# Check if doctor exists and is active
		if self.doctor:
			practitioner = frappe.get_doc("Healthcare Practitioner", self.doctor)
			if hasattr(practitioner, 'practitioner_name') and not practitioner.practitioner_name:
				frappe.throw(_("Doctor {0} is not properly configured").format(self.doctor))
	
	def validate_medication_schedule(self):
		"""Validate medication is S4 (Schedule 4)"""
		if self.medication:
			medication = frappe.get_doc("Medication", self.medication)
			# Check if medication is GLP-1 or S4
			# This is a simplified check - adjust based on your Medication structure
			if hasattr(medication, 'schedule') and medication.schedule:
				if medication.schedule not in ["S4", "Schedule 4"]:
					frappe.throw(_("Medication must be Schedule 4 (S4) for GLP-1 prescriptions"))
	
	def validate_quantity_limits(self):
		"""Validate quantity does not exceed 30 days for compounding"""
		if self.quantity and self.duration:
			# Parse duration to days (simplified - adjust based on your duration format)
			# Max 30 days for compounding per SAHPRA regulations
			if "30" in str(self.duration) or "month" in str(self.duration).lower():
				if self.quantity > 30:
					frappe.throw(_("Quantity cannot exceed 30 days supply for compounding"))
	
	def validate_immutable_fields(self):
		"""Ensure prescription cannot be edited after approval"""
		if self.status in ["Doctor Approved", "Dispensed", "Closed"]:
			# Check if critical fields are being changed
			old_doc = self.get_doc_before_save()
			if old_doc:
				immutable_fields = ["patient", "medication", "dosage", "quantity", "doctor"]
				for field in immutable_fields:
					if hasattr(old_doc, field) and getattr(old_doc, field) != getattr(self, field):
						frappe.throw(_("Cannot modify {0} after prescription approval").format(field))
	
	def on_update_after_submit(self):
		"""Block updates after submission"""
		if self.status in ["Doctor Approved", "Dispensed", "Closed"]:
			frappe.throw(_("Prescription cannot be modified after approval"))
