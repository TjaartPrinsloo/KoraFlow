# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class PharmacyWarehouse(Document):
	def validate(self):
		"""Validate warehouse configuration"""
		if self.warehouse_type == "Physical" and self.is_licensed and not self.pharmacy_license_number:
			frappe.throw(_("Pharmacy License Number is required for licensed physical warehouses"))
		
		# Ensure ERPNext warehouse exists
		if self.erpnext_warehouse:
			if not frappe.db.exists("Warehouse", self.erpnext_warehouse):
				frappe.throw(_("ERPNext Warehouse {0} does not exist").format(self.erpnext_warehouse))
	
	def on_update(self):
		"""Update ERPNext warehouse settings"""
		if self.erpnext_warehouse:
			# Update warehouse custom fields if needed
			warehouse = frappe.get_doc("Warehouse", self.erpnext_warehouse)
			if hasattr(warehouse, 'custom_is_pharmacy_warehouse'):
				warehouse.db_set('custom_is_pharmacy_warehouse', 1)
			if hasattr(warehouse, 'custom_is_licensed') and self.is_licensed:
				warehouse.db_set('custom_is_licensed', 1)
			if hasattr(warehouse, 'custom_cold_chain_enabled') and self.cold_chain_enabled:
				warehouse.db_set('custom_cold_chain_enabled', 1)
