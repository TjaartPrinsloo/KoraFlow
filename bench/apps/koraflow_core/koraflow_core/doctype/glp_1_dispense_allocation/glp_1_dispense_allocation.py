# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1DispenseAllocation(Document):
	def validate(self):
		"""Validate allocation - this is virtual only, cannot reduce physical stock"""
		if self.virtual_warehouse:
			# Verify warehouse is registered in Pharmacy Warehouse
			pharm_warehouse = frappe.db.get_value(
				"Pharmacy Warehouse",
				{"erpnext_warehouse": self.virtual_warehouse},
				"warehouse_type"
			)
			if pharm_warehouse and pharm_warehouse != "Virtual":
				frappe.throw(_("Allocation can only use virtual warehouses, not physical warehouses"))
			# If warehouse is not in Pharmacy Warehouse at all, allow it
			# (generic ERPNext warehouses can be used for allocation)
	
	def on_submit(self):
		"""Allocation is logical only - no physical stock movement"""
		# This is a reservation, not actual stock movement
		pass
