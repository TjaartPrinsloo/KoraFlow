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
		
		# Auto-create Quotation
		self.create_quotation()

	def on_update(self):
		"""Handle updates (e.g. status change on save)"""
		self.create_quotation()

	def create_quotation(self):
		"""Create a quotation for the prescribed medication"""
		frappe.log_error(title="Quotation Debug", message=f"Creating Quotation for {self.name}, Status: {self.status}")
		
		if self.status != "Doctor Approved":
			frappe.log_error(title="Quotation Debug", message=f"Status mismatch: {self.status}")
			return
			
		# Check if quotation already exists
		existing_qty = frappe.db.get_value("Quotation", {"custom_prescription": self.name}, "name")
		if existing_qty:
			frappe.log_error(title="Quotation Debug", message=f"Quotation exists: {existing_qty}")
			return

		patient = frappe.get_doc("Patient", self.patient)
		if not patient.customer:
			# Create customer if missing
			customer = frappe.new_doc("Customer")
			customer.customer_name = patient.patient_name
			customer.customer_type = "Individual"
			customer.customer_group = "Individual"
			customer.save(ignore_permissions=True)
			
			# Link to patient
			patient.customer = customer.name
			patient.save(ignore_permissions=True)
			frappe.log_error(title="Quotation Debug", message=f"Created Customer: {customer.name}")
		
		# Get Item from Medication (Child Table: linked_items)
		# medication -> linked_items (Medication Linked Item) -> item
		linked_item = frappe.get_all("Medication Linked Item", filters={"parent": self.medication}, fields=["item"], limit=1)
		
		if not linked_item or not linked_item[0].item:
			frappe.log_error(title="Quotation Debug", message=f"No Linked Item found for {self.medication}")
			frappe.msgprint(_("Warning: No Linked Item found for Medication {0}. Cannot create Quotation.").format(self.medication))
			return
			
		item_code = linked_item[0].item
		frappe.log_error(title="Quotation Debug", message=f"Found Item: {item_code}")

		# Create Quotation
		quotation = frappe.new_doc("Quotation")
		quotation.quotation_to = "Customer"
		quotation.party_name = patient.customer
		quotation.transaction_date = frappe.utils.today()
		quotation.valid_till = frappe.utils.add_days(frappe.utils.today(), 30)
		quotation.company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
		quotation.custom_prescription = self.name
		
		# Add Item
		price = frappe.get_all("Item Price", filters={"item_code": item_code, "price_list": "Standard Selling"}, fields=["price_list_rate"], limit=1)
		rate = price[0].price_list_rate if price else 0
		
		quotation.append("items", {
			"item_code": item_code,
			"qty": self.quantity or 1,
			"rate": rate 
		})
		
		quotation.save(ignore_permissions=True)
		# Link back
		frappe.db.set_value(self.doctype, self.name, "linked_quotation", quotation.name)
		frappe.msgprint(_("Quotation {0} created").format(quotation.name), alert=True)
	
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
