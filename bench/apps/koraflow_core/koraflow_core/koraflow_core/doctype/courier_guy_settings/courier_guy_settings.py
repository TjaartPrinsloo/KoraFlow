"""
Courier Guy Settings Controller
"""
import frappe
from frappe.model.document import Document


class CourierGuySettings(Document):
	def validate(self):
		"""Validate settings"""
		if self.enabled and not self.api_key:
			frappe.throw("API Key is required when Courier Guy integration is enabled")
		
		if self.enabled and not self.api_url:
			frappe.throw("API URL is required when Courier Guy integration is enabled")


def get_settings():
	"""Get Courier Guy Settings (singleton)"""
	settings = frappe.get_single("Courier Guy Settings")
	if not settings.enabled:
		frappe.throw("Courier Guy integration is not enabled. Please enable it in Courier Guy Settings.")
	return settings

