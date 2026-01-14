# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1ComplianceAuditLog(Document):
	def validate(self):
		"""Audit logs are immutable - prevent modifications"""
		if not self.is_new():
			frappe.throw(_("Audit logs cannot be modified"))
	
	def before_insert(self):
		"""Set timestamp if not provided"""
		if not self.timestamp:
			from frappe.utils import now
			self.timestamp = now()
	
	def on_update(self):
		"""Block updates to audit logs"""
		frappe.throw(_("Audit logs are immutable and cannot be modified"))
