# Copyright (c) 2025, KoraFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PatientVital(Document):
	def before_save(self):
		self.calculate_bmi()

	def calculate_bmi(self):
		if self.weight_kg and self.height_cm:
			height_m = self.height_cm / 100.0
			self.bmi = round(self.weight_kg / (height_m * height_m), 2)
