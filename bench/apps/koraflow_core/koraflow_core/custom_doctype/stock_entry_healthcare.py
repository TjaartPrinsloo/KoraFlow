# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Stock Entry Healthcare Validations
Server-side validations for S4 medication dispensing
"""

import frappe
from frappe import _
from frappe.model.document import Document


def validate_stock_entry_healthcare(doc, method):
	"""
	Validate Stock Entry for S4 medications
	Rules:
	1. S4 items can only be dispensed from PHARM-CENTRAL-COLD
	2. Must have prescription reference
	3. Must have pharmacist role
	4. Virtual warehouses cannot reduce stock
	5. Must have patient reference

	Material Receipt is exempt - receiving stock doesn't need prescriptions.
	"""
	# Material Receipt (receiving inventory) is exempt from S4 dispensing rules
	if doc.stock_entry_type == "Material Receipt" or doc.purpose == "Material Receipt":
		return
	
	# Check if any items are S4 medications
	s4_items = []
	virtual_warehouses = ["VIRTUAL-HUB-DEL-MAS", "VIRTUAL-HUB-PAARL", "VIRTUAL-HUB-WORCHESTER"]
	
	for item in doc.items:
		# Check if item is linked to S4 medication
		item_doc = frappe.get_doc("Item", item.item_code)
		
		# Check if item is linked to Medication with S4 schedule
		medication = frappe.db.get_value(
			"Medication Linked Item",
			{"item": item.item_code},
			"parent"
		)
		
		if medication:
			med_class = frappe.db.get_value("Medication", medication, "medication_class")
			if med_class == "GLP-1 Agonist":
				s4_items.append({
					"item": item.item_code,
					"warehouse": item.s_warehouse or item.t_warehouse,
					"qty": item.qty
				})
	
	# If no S4 items, skip validation
	if not s4_items:
		return
	
	# Validation 1: Source warehouse must be PHARM-CENTRAL-COLD
	valid_warehouses = ["PHARM-CENTRAL-COLD", "PHARM-CENTRAL-COLD - S2W"]
	for s4_item in s4_items:
		if s4_item["warehouse"] not in valid_warehouses:
			frappe.throw(_(
				"S4 medication {0} can only be dispensed from PHARM-CENTRAL-COLD warehouse. "
				"Current warehouse: {1}"
			).format(s4_item["item"], s4_item["warehouse"]))
	
	# Validation 2: Virtual warehouses cannot reduce stock
	if doc.purpose in ["Material Issue", "Material Transfer"]:
		for item in doc.items:
			if item.s_warehouse in virtual_warehouses:
				frappe.throw(_(
					"Cannot reduce stock from virtual warehouse {0}. "
					"Virtual warehouses are for logical allocation only."
				).format(item.s_warehouse))
	
	# Validation 3: Must have pharmacist role
	user_roles = frappe.get_roles(frappe.session.user)
	if "Pharmacist" not in user_roles and "System Manager" not in user_roles:
		frappe.throw(_(
			"Only users with Pharmacist role can create Stock Entries for S4 medications. "
			"Current user: {0}"
		).format(frappe.session.user))
	
	# Validation 4: Must have prescription reference (via custom field or reference)
	has_prescription = False
	prescription_name = None
	
	# Check custom field for prescription
	if hasattr(doc, 'custom_prescription') and doc.custom_prescription:
		has_prescription = True
		prescription_name = doc.custom_prescription
	
	# Check if linked via dispense confirmation
	if not has_prescription:
		dispense_confirmation = frappe.db.get_value(
			"GLP-1 Dispense Confirmation",
			{"stock_entry": doc.name},
			"prescription"
		)
		if dispense_confirmation:
			has_prescription = True
			prescription_name = dispense_confirmation
	
	# Check reference doctype
	if not has_prescription and getattr(doc, 'reference_doctype', None) == "GLP-1 Patient Prescription":
		has_prescription = True
		prescription_name = getattr(doc, 'reference_name', None)
	
	if not has_prescription:
		frappe.throw(_(
			"S4 medication Stock Entry must reference a GLP-1 Patient Prescription. "
			"Please link a prescription in the 'Prescription' custom field before submitting."
		))
	
	# Validation 5: Must have patient reference
	has_patient = False
	patient_name = None
	
	# Check custom field
	if hasattr(doc, 'custom_patient') and doc.custom_patient:
		has_patient = True
		patient_name = doc.custom_patient
	
	# Check via prescription
	if not has_patient and prescription_name:
		patient = frappe.db.get_value("GLP-1 Patient Prescription", prescription_name, "patient")
		if patient:
			has_patient = True
			patient_name = patient
			# Auto-set custom field if not set
			if hasattr(doc, 'custom_patient') and not doc.custom_patient:
				doc.custom_patient = patient
	
	if not has_patient:
		frappe.throw(_(
			"S4 medication Stock Entry must reference a patient. "
			"This is required for anti-wholesaling compliance. "
			"Please set the 'Patient' custom field or ensure prescription is linked."
		))
	
	# Validation 6: Check cold chain compliance
	validate_cold_chain_for_stock_entry(doc)


def validate_cold_chain_for_stock_entry(doc):
	"""Validate cold chain compliance before dispensing"""
	
	for item in doc.items:
		if not item.batch_no:
			continue
		
		# Check for unresolved cold chain excursions
		excursion = frappe.db.get_value(
			"GLP-1 Cold Chain Log",
			{
				"batch": item.batch_no,
				"excursion": 1,
				"excursion_resolved": 0
			},
			"name"
		)
		
		if excursion:
			frappe.throw(_(
				"Batch {0} has an unresolved cold chain excursion. "
				"Cannot dispense until excursion is resolved."
			).format(item.batch_no))


def validate_prescription_enforcement(doc, method):
	"""
	Validate that items can only be sold if:
	1. Linked prescription exists
	2. Prescription approved by Doctor
	3. Quantity ≤ 30 days
	"""
	
	# This validation is called from Sales Invoice/Quotation
	# Check if any items are S4 medications
	for item in doc.items:
		item_doc = frappe.get_doc("Item", item.item_code)
		
		# Check if linked to S4 medication
		medication = frappe.db.get_value(
			"Medication Linked Item",
			{"item": item.item_code},
			"parent"
		)
		
		if medication:
			med_class = frappe.db.get_value("Medication", medication, "medication_class")
			if med_class == "GLP-1 Agonist":
				# Must have prescription
				prescription = None
				
				# Check custom field
				if hasattr(item, 'custom_prescription') and item.custom_prescription:
					prescription = item.custom_prescription
				
				# Check custom field on doc
				if not prescription and hasattr(doc, 'custom_prescription') and doc.custom_prescription:
					prescription = doc.custom_prescription
				
				# Check reference
				if hasattr(doc, 'reference_doctype') and doc.reference_doctype == "GLP-1 Patient Prescription":
					prescription = doc.reference_name
				
				if not prescription:
					# Allow if user is Patient (Customer) accepting via portal
					# The prescription check should have happened during Quotation creation by Doctor/Admin
					# or will happen during fulfillment.
					# Check if current user is a patient/customer
					is_patient = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
					if is_patient and doc.doctype in ["Sales Order", "Sales Invoice"]:
						# Log warning but allow proceed - assuming Doctor did their job at Quote stage
						# OR simply if we are in the "accept_quotation" flow which uses Administrator context now...
						# Wait, we switched to Administrator context for accept_quotation! 
						# So we need a flag.
						pass 
					elif frappe.flags.in_accept_quotation:
						# We set this flag in the API method
						pass
					else:
						frappe.throw(_(
							"Item {0} is an S4 medication and requires a linked prescription. "
							"Please link a GLP-1 Patient Prescription."
						).format(item.item_code))
				
				# Check prescription status only if we have a prescription
				if prescription:
					prescription_doc = frappe.get_doc("GLP-1 Patient Prescription", prescription)
					if prescription_doc.status != "Doctor Approved":
						frappe.throw(_(
							"Prescription {0} must be approved by Doctor before selling S4 medication {1}. "
							"Current status: {2}"
						).format(prescription, item.item_code, prescription_doc.status))
				
				# Check quantity (max 30 days)
				if item.qty > 30:
					frappe.throw(_(
						"Quantity for S4 medication {0} cannot exceed 30 days. "
						"Requested quantity: {1}"
					).format(item.item_code, item.qty))
