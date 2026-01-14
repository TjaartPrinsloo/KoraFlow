# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Custom Stock Entry for GLP-1 Dispensing
Enforces GLP-1 dispensing rules and warehouse restrictions
"""

import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from koraflow_core.utils.glp1_compliance import (
	validate_cold_chain_before_dispense,
	validate_patient_reference,
	check_role_isolation
)


class GLP1StockEntry(StockEntry):
	def validate(self):
		"""Override validate to add GLP-1 compliance checks"""
		super().validate()
		
		# Check if this is a GLP-1 dispense
		if self.purpose == "Material Issue":
			self.validate_glp1_dispense()
	
	def validate_glp1_dispense(self):
		"""Validate GLP-1 dispensing rules"""
		# Get PHARM-CENTRAL-COLD warehouse
		pharm_warehouse = frappe.db.get_value(
			"Pharmacy Warehouse",
			{"warehouse_name": "PHARM-CENTRAL-COLD"},
			"erpnext_warehouse"
		)
		
		if not pharm_warehouse:
			return  # GLP-1 warehouses not set up yet
		
		# Check if any items are from PHARM-CENTRAL-COLD
		is_glp1_dispense = False
		for item in self.items:
			if item.s_warehouse == pharm_warehouse:
				is_glp1_dispense = True
				break
		
		if not is_glp1_dispense:
			return  # Not a GLP-1 dispense
		
		# CP-E: Anti-Wholesaling Guard - Patient must be referenced
		patient_check = validate_patient_reference(self.doctype, self.name)
		if not patient_check.get("valid"):
			frappe.throw(_("GLP-1 dispense must reference a patient"))
		
		# CP-C: Cold Chain Enforcement
		for item in self.items:
			if item.s_warehouse == pharm_warehouse and item.batch_no:
				validate_cold_chain_before_dispense(item.batch_no)
		
		# CP-D: Role Isolation - Only pharmacists can dispense
		user_roles = frappe.get_roles(frappe.session.user)
		if "Pharmacist" not in user_roles and "System Manager" not in user_roles:
			frappe.throw(_("Only pharmacists can dispense GLP-1 medications"))
		
		# Ensure source warehouse is PHARM-CENTRAL-COLD
		for item in self.items:
			if item.s_warehouse and item.s_warehouse != pharm_warehouse:
				# Check if it's a virtual warehouse (allowed for allocation)
				pharm_warehouse_type = frappe.db.get_value(
					"Pharmacy Warehouse",
					{"erpnext_warehouse": item.s_warehouse},
					"warehouse_type"
				)
				if pharm_warehouse_type == "Virtual":
					frappe.throw(_("Cannot dispense from virtual warehouse. All GLP-1 stock must be dispensed from PHARM-CENTRAL-COLD"))
	
	def before_submit(self):
		"""Additional checks before submit"""
		super().before_submit()
		
		if self.purpose == "Material Issue":
			# Ensure patient reference is set
			if not hasattr(self, 'custom_patient') or not self.custom_patient:
				# Try to get from linked allocation
				allocation = frappe.db.get_value(
					"GLP-1 Dispense Allocation",
					{"status": "Reserved"},
					"patient",
					order_by="creation desc",
					limit=1
				)
				if allocation:
					if not hasattr(self, 'custom_patient'):
						# Add custom field if it doesn't exist
						pass  # Custom fields need to be added via Customize Form
					else:
						self.custom_patient = allocation
