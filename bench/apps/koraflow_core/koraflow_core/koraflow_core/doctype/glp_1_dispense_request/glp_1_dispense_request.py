# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1DispenseRequest(Document):
	def validate(self):
		"""Validate dispense request - this is a signal only, not stock movement"""
		if self.prescription:
			prescription = frappe.get_doc("GLP-1 Patient Prescription", self.prescription)
			if prescription.status != "Doctor Approved":
				frappe.throw(_("Prescription must be approved before dispense request"))
		
		# Ensure this does not trigger stock movement
		# This is just a signal to pharmacy
	
	def on_submit(self):
		"""Create pharmacy review on submit"""
		# This will be handled by workflow hooks
		pass
