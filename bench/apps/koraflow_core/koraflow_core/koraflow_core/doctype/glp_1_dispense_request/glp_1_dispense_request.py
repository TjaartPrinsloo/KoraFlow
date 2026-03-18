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
			# Allow any post-approval status in the workflow
			approved_statuses = ("Doctor Approved", "Quoted", "Dispense Queued", "Dispensed", "Shipped", "Delivered", "Closed")
			if prescription.status not in approved_statuses:
				frappe.throw(_("Prescription must be approved before dispense request. Current status: {0}").format(prescription.status))
		
		# Ensure this does not trigger stock movement
		# This is just a signal to pharmacy
	
	def on_submit(self):
		"""Create pharmacy review on submit"""
		# This will be handled by workflow hooks
		pass
