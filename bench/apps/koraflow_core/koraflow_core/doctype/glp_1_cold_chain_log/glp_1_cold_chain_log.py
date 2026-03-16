# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1ColdChainLog(Document):
	def validate(self):
		"""Validate temperature and excursion"""
		# GLP-1 medications typically require 2-8°C storage
		if self.temperature:
			if self.temperature < 2 or self.temperature > 8:
				if not self.excursion:
					self.excursion = 1
					frappe.msgprint(_("Temperature excursion detected: {0}°C (acceptable range: 2-8°C)").format(self.temperature))
	
	def on_update(self):
		"""Check if unresolved excursions exist for this batch"""
		if self.excursion and not self.excursion_resolved:
			# This will be checked by compliance checkpoints before dispensing
			pass
