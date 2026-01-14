# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Setup script for GLP-1 items
Configures items with batch tracking, expiry, and cold chain flags
"""

import frappe
from frappe import _


def setup_glp1_items():
	"""Configure GLP-1 items with required settings"""
	
	glp1_items = [
		{
			"item_code": "GLP1-SEMAGLUTIDE-001",
			"item_name": "Semaglutide 2.5mg",
			"description": "GLP-1 Agonist - Semaglutide",
			"item_group": "Pharmaceuticals",
			"stock_uom": "Nos",
			"has_batch_no": 1,
			"create_new_batch": 1,
			"has_expiry_date": 1,
			"has_serial_no": 0,
			"is_stock_item": 1,
			"is_sales_item": 1,
			"is_purchase_item": 1
		},
		{
			"item_code": "GLP1-TIRZEPATIDE-001",
			"item_name": "Tirzepatide 5mg",
			"description": "GLP-1/GIP Agonist - Tirzepatide",
			"item_group": "Pharmaceuticals",
			"stock_uom": "Nos",
			"has_batch_no": 1,
			"create_new_batch": 1,
			"has_expiry_date": 1,
			"has_serial_no": 0,
			"is_stock_item": 1,
			"is_sales_item": 1,
			"is_purchase_item": 1
		}
	]
	
	for item_data in glp1_items:
		create_or_update_glp1_item(item_data)
	
	frappe.msgprint(_("GLP-1 items configured successfully"))


def create_or_update_glp1_item(item_data):
	"""Create or update GLP-1 item with required settings"""
	item_code = item_data["item_code"]
	
	if frappe.db.exists("Item", item_code):
		item = frappe.get_doc("Item", item_code)
		update_required = False
	else:
		item = frappe.get_doc({"doctype": "Item"})
		update_required = True
	
	# Set all fields
	for key, value in item_data.items():
		if hasattr(item, key):
			setattr(item, key, value)
	
	# GLP-1 specific settings
	item.has_batch_no = 1
	item.create_new_batch = 1
	item.has_expiry_date = 1
	
	# Add custom fields if they exist
	if hasattr(item, 'custom_cold_chain_required'):
		item.custom_cold_chain_required = 1
	if hasattr(item, 'custom_schedule'):
		item.custom_schedule = "S4"
	if hasattr(item, 'custom_glp1_medication'):
		item.custom_glp1_medication = 1
	
	if update_required:
		item.insert(ignore_permissions=True)
	else:
		item.save(ignore_permissions=True)
	
	frappe.db.commit()
	
	return item.name


if __name__ == "__main__":
	setup_glp1_items()
