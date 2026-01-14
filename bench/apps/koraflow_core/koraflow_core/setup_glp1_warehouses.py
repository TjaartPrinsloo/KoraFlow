# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Setup script for GLP-1 dispensing warehouses
Creates PHARM-CENTRAL-COLD (physical licensed warehouse) and virtual clinic warehouses
"""

import frappe
from frappe import _


def setup_glp1_warehouses():
	"""Create GLP-1 dispensing warehouse structure"""
	
	# Create PHARM-CENTRAL-COLD (Physical Licensed Warehouse)
	create_pharm_central_cold()
	
	# Create virtual clinic warehouses (examples - can be customized)
	create_virtual_warehouses()
	
	frappe.msgprint(_("GLP-1 warehouse structure created successfully"))


def create_pharm_central_cold():
	"""Create the central licensed pharmacy warehouse"""
	warehouse_name = "PHARM-CENTRAL-COLD"
	
	# Check if already exists
	if frappe.db.exists("Pharmacy Warehouse", warehouse_name):
		frappe.msgprint(_("Pharmacy Warehouse {0} already exists").format(warehouse_name))
		return
	
	# Create ERPNext Warehouse first
	erpnext_warehouse_name = "PHARM-CENTRAL-COLD"
	if not frappe.db.exists("Warehouse", erpnext_warehouse_name):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": erpnext_warehouse_name,
			"company": frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {"is_group": 0}, "name"),
			"is_group": 0
		})
		warehouse.insert(ignore_permissions=True)
		frappe.db.commit()
	
	# Create Pharmacy Warehouse
	pharm_warehouse = frappe.get_doc({
		"doctype": "Pharmacy Warehouse",
		"warehouse_name": warehouse_name,
		"erpnext_warehouse": erpnext_warehouse_name,
		"warehouse_type": "Physical",
		"is_licensed": 1,
		"pharmacy_license_number": "PHARM-LICENSE-001",  # Update with actual license
		"cold_chain_enabled": 1,
		"description": "Central licensed pharmacy warehouse for GLP-1 medications. All physical stock must be dispensed from this warehouse.",
		"is_active": 1
	})
	pharm_warehouse.insert(ignore_permissions=True)
	frappe.db.commit()
	
	frappe.msgprint(_("Created {0} warehouse").format(warehouse_name))


def create_virtual_warehouses():
	"""Create virtual clinic warehouses for operational modeling"""
	virtual_warehouses = [
		{
			"name": "VIRTUAL-CLINIC-001",
			"description": "Virtual warehouse for Clinic 001 - operational grouping only"
		},
		{
			"name": "VIRTUAL-CLINIC-002",
			"description": "Virtual warehouse for Clinic 002 - operational grouping only"
		}
	]
	
	for vw in virtual_warehouses:
		if frappe.db.exists("Pharmacy Warehouse", vw["name"]):
			continue
		
		# Create ERPNext Warehouse (virtual)
		erpnext_name = vw["name"]
		if not frappe.db.exists("Warehouse", erpnext_name):
			warehouse = frappe.get_doc({
				"doctype": "Warehouse",
				"warehouse_name": erpnext_name,
				"company": frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {"is_group": 0}, "name"),
				"is_group": 0
			})
			warehouse.insert(ignore_permissions=True)
			frappe.db.commit()
		
		# Create Pharmacy Warehouse (virtual)
		pharm_warehouse = frappe.get_doc({
			"doctype": "Pharmacy Warehouse",
			"warehouse_name": vw["name"],
			"erpnext_warehouse": erpnext_name,
			"warehouse_type": "Virtual",
			"is_licensed": 0,
			"cold_chain_enabled": 0,
			"description": vw["description"],
			"is_active": 1
		})
		pharm_warehouse.insert(ignore_permissions=True)
		frappe.db.commit()


if __name__ == "__main__":
	setup_glp1_warehouses()
