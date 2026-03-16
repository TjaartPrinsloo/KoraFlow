# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1PharmacyReview(Document):
	def validate(self):
		"""Validate pharmacist has Pharmacist role"""
		if self.pharmacist:
			user = frappe.get_doc("User", self.pharmacist)
			user_roles = [r.role for r in user.roles]
			if "Pharmacist" not in user_roles and "System Manager" not in user_roles:
				frappe.throw(_("User must have Pharmacist role to perform pharmacy review"))
		
		if not self.pharmacist_license_number:
			frappe.throw(_("Pharmacist License Number is required"))
	
	def on_submit(self):
		"""Create audit log on approval"""
		if self.review_status == "Approved":
			from koraflow_core.utils.glp1_compliance import create_audit_log
			create_audit_log(
				event_type="Review",
				reference_doctype="GLP-1 Pharmacy Review",
				reference_name=self.name,
				actor=self.pharmacist,
				actor_license=self.pharmacist_license_number,
				details={"review_status": self.review_status}
			)
