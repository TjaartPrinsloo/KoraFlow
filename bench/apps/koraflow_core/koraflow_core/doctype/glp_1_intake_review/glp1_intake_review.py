# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1IntakeReview(Document):
	def validate(self):
		"""Validate reviewer has Nurse role"""
		if self.reviewer:
			user = frappe.get_doc("User", self.reviewer)
			user_roles = [r.role for r in user.roles]
			if "Nurse" not in user_roles and "System Manager" not in user_roles:
				frappe.throw(_("Reviewer must have Nurse role"))
	
	def on_update(self):
		"""Validate suggested prescription is draft only"""
		if self.suggested_prescription and self.status == "Approved":
			prescription = frappe.get_doc("GLP-1 Patient Prescription", self.suggested_prescription)
			if prescription.status != "Draft":
				frappe.throw(_("Suggested prescription must be in Draft status only"))
