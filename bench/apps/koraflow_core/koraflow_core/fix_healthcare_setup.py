# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Fix Healthcare Dispensing System Setup Issues
- Fix medicine defaults (7 day interval, 30 day duration)
- Fill in Item drug specifications
- Ensure Healthcare Practitioner records exist
- Verify warehouse requirements
"""

import frappe
from frappe import _


def fix_medicine_defaults():
	"""Fix medicine default interval and duration settings"""
	
	medicines = ["Eco", "Gold", "Aminowell", "Eco Boost", "RUBY", "Titanium", "Ruby Boost"]
	
	# Get or create Prescription Duration "30 Days"
	prescription_duration = "30 Days"
	if not frappe.db.exists("Prescription Duration", prescription_duration):
		try:
			frappe.get_doc({
				"doctype": "Prescription Duration",
				"duration": prescription_duration
			}).insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(_("Created Prescription Duration: {0}").format(prescription_duration))
		except Exception as e:
			frappe.log_error(f"Could not create Prescription Duration: {str(e)}", "Medicine Setup Fix")
	
	for med_name in medicines:
		if frappe.db.exists("Medication", med_name):
			medication = frappe.get_doc("Medication", med_name)
			
			# Set dosage_by_interval = 1 to enable interval-based dosing
			medication.dosage_by_interval = 1
			medication.default_interval = 7
			medication.default_interval_uom = "Day"
			
			# Set default prescription duration (if not using interval)
			# But since we're using interval, this might not be required
			# However, set it anyway for compatibility
			if prescription_duration and frappe.db.exists("Prescription Duration", prescription_duration):
				medication.default_prescription_duration = prescription_duration
			
			medication.save(ignore_permissions=True)
			frappe.msgprint(_("Updated Medication: {0} - Interval: 7 Days, Duration: 30 Days").format(med_name))
	
	frappe.db.commit()


def fix_item_drug_specifications():
	"""Fill in Item drug specifications from Medication data"""
	
	# Get or create Volume UOM
	volume_uom = "ml"
	if not frappe.db.exists("UOM", volume_uom):
		frappe.get_doc({
			"doctype": "UOM",
			"uom_name": volume_uom
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	
	medicines = ["Eco", "Gold", "Aminowell", "Eco Boost", "RUBY", "Titanium", "Ruby Boost"]
	
	for med_name in medicines:
		# Get medication data
		if not frappe.db.exists("Medication", med_name):
			continue
		
		medication = frappe.get_doc("Medication", med_name)
		
		# Get linked item
		if not frappe.db.exists("Item", med_name):
			continue
		
		item = frappe.get_doc("Item", med_name)
		
		# Fill in drug specifications
		item.generic_name = med_name
		item.strength = medication.strength or 2.5
		item.strength_uom = medication.strength_uom or "mg"
		item.dosage_form = medication.dosage_form or "Injection"
		item.route_of_administration = "Subcutaneous"
		item.volume = 0.8
		item.volume_uom = volume_uom
		# Legal status should be "Controlled Substance" for S4
		item.legal_status = "Controlled Substance"
		# Product control - check if field exists and set appropriately
		if hasattr(item, 'product_control'):
			item.product_control = "Controlled"
		item.is_prescription_item = 1
		item.is_controlled_substance = 1
		
		item.save(ignore_permissions=True)
		frappe.msgprint(_("Updated Item Drug Specifications: {0}").format(med_name))
	
	frappe.db.commit()


def ensure_healthcare_practitioners():
	"""Ensure Healthcare Practitioner DocType records exist for users with Healthcare Practitioner role"""
	
	# Get users with Healthcare Practitioner role
	users_with_role = frappe.get_all(
		"Has Role",
		filters={"role": "Healthcare Practitioner"},
		fields=["parent"]
	)
	
	if not frappe.db.exists("DocType", "Healthcare Practitioner"):
		frappe.msgprint(_("Healthcare Practitioner DocType does not exist. Skipping practitioner creation."))
		return
	
	for user_role in users_with_role:
		user_email = user_role.parent
		
		# Check if Healthcare Practitioner record exists by user_id
		existing_practitioner = frappe.db.get_value(
			"Healthcare Practitioner",
			{"user_id": user_email},
			"name"
		)
		
		# Also try by practitioner name
		if not existing_practitioner:
			user = frappe.get_doc("User", user_email)
			practitioner_name = f"{user.first_name} {user.last_name}"
			existing_practitioner = frappe.db.get_value(
				"Healthcare Practitioner",
				{"practitioner_name": practitioner_name},
				"name"
			)
		
		if not existing_practitioner:
			# Get user details
			user = frappe.get_doc("User", user_email)
			practitioner_name = f"{user.first_name} {user.last_name}"
			
			# Create Healthcare Practitioner record
			try:
				practitioner_data = {
					"doctype": "Healthcare Practitioner",
					"first_name": user.first_name,
					"last_name": user.last_name,
					"practitioner_name": practitioner_name,
					"status": "Active"
				}
				
				# Add user_id field (standard field in Healthcare Practitioner)
				practitioner_data["user_id"] = user_email
				
				practitioner = frappe.get_doc(practitioner_data)
				practitioner.insert(ignore_permissions=True)
				frappe.msgprint(_("Created Healthcare Practitioner: {0}").format(practitioner_name))
			except Exception as e:
				frappe.log_error(f"Could not create Healthcare Practitioner for {user_email}: {str(e)}", "Practitioner Setup")
	
	frappe.db.commit()


def verify_warehouse_requirements():
	"""Verify warehouses meet all requirements"""
	
	# Physical warehouse requirements
	pharm_warehouse_name = "PHARM-CENTRAL-COLD"
	pharm_warehouse = frappe.db.get_value(
		"Warehouse",
		{"warehouse_name": pharm_warehouse_name},
		"name"
	)
	
	if pharm_warehouse:
		warehouse = frappe.get_doc("Warehouse", pharm_warehouse)
		
		# Verify requirements
		issues = []
		
		# Should not be a group warehouse
		if warehouse.is_group:
			issues.append("Should not be a group warehouse")
		
		# Check if allow_negative_stock field exists
		if hasattr(warehouse, 'allow_negative_stock'):
			if warehouse.allow_negative_stock:
				warehouse.allow_negative_stock = 0
				warehouse.save(ignore_permissions=True)
				frappe.msgprint(_("Fixed: PHARM-CENTRAL-COLD - Disabled negative stock"))
		
		# Check Pharmacy Warehouse record
		if frappe.db.exists("DocType", "Pharmacy Warehouse"):
			pharm_wh_record = frappe.db.get_value(
				"Pharmacy Warehouse",
				{"warehouse_name": pharm_warehouse_name},
				"name"
			)
			if pharm_wh_record:
				pharm_wh = frappe.get_doc("Pharmacy Warehouse", pharm_wh_record)
				if not pharm_wh.cold_chain_enabled:
					pharm_wh.cold_chain_enabled = 1
					pharm_wh.save(ignore_permissions=True)
					frappe.msgprint(_("Fixed: PHARM-CENTRAL-COLD - Enabled cold chain"))
				if not pharm_wh.is_licensed:
					pharm_wh.is_licensed = 1
					pharm_wh.save(ignore_permissions=True)
					frappe.msgprint(_("Fixed: PHARM-CENTRAL-COLD - Set as licensed"))
	
	# Virtual warehouses - should not allow negative stock
	virtual_warehouses = ["VIRTUAL-HUB-DEL-MAS", "VIRTUAL-HUB-PAARL", "VIRTUAL-HUB-WORCHESTER"]
	
	for vw_name in virtual_warehouses:
		vw = frappe.db.get_value("Warehouse", {"warehouse_name": vw_name}, "name")
		if vw:
			warehouse = frappe.get_doc("Warehouse", vw)
			if hasattr(warehouse, 'allow_negative_stock'):
				if warehouse.allow_negative_stock:
					warehouse.allow_negative_stock = 0
					warehouse.save(ignore_permissions=True)
					frappe.msgprint(_("Fixed: {0} - Disabled negative stock").format(vw_name))
	
	frappe.db.commit()


def fix_all_issues():
	"""Run all fixes"""
	
	print("\n" + "="*60)
	print("FIXING HEALTHCARE DISPENSING SETUP ISSUES")
	print("="*60)
	
	print("\n1. Fixing Medicine Defaults...")
	fix_medicine_defaults()
	
	print("\n2. Filling Item Drug Specifications...")
	fix_item_drug_specifications()
	
	print("\n3. Ensuring Healthcare Practitioners...")
	ensure_healthcare_practitioners()
	
	print("\n4. Verifying Warehouse Requirements...")
	verify_warehouse_requirements()
	
	print("\n" + "="*60)
	print("✅ ALL FIXES COMPLETED")
	print("="*60)


if __name__ == "__main__":
	fix_all_issues()
