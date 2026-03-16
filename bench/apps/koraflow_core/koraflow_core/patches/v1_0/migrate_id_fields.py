"""
Migrate existing id_number__passport_number values to new separate fields
"""
import frappe
import re


def is_valid_sa_id(id_number):
	"""Check if the ID number is a valid SA ID using Luhn algorithm"""
	if not id_number or len(id_number) != 13:
		return False
	
	if not id_number.isdigit():
		return False
	
	# Check date validity
	try:
		mm = int(id_number[2:4])
		dd = int(id_number[4:6])
		if mm < 1 or mm > 12:
			return False
		if dd < 1 or dd > 31:
			return False
	except ValueError:
		return False
	
	# Luhn algorithm check
	total = 0
	for i, digit in enumerate(id_number):
		d = int(digit)
		if i % 2 == 1:
			d *= 2
			if d > 9:
				d -= 9
		total += d
	
	return total % 10 == 0


def execute():
	"""Migrate existing ID data to new fields"""

	# Migrate GLP-1 Intake Submission records
	# Skip gracefully if the table or column doesn't exist yet (fresh install)
	try:
		submissions = frappe.db.sql("""
			SELECT name, id_number__passport_number
			FROM `tabGLP-1 Intake Submission`
			WHERE id_number__passport_number IS NOT NULL
			AND id_number__passport_number != ''
			AND (sa_id_number IS NULL OR sa_id_number = '')
			AND (passport_number IS NULL OR passport_number = '')
		""", as_dict=True)
	except Exception:
		submissions = []

	migrated_sa_id = 0
	migrated_passport = 0

	for sub in submissions:
		id_value = sub.id_number__passport_number.strip()
		
		if is_valid_sa_id(id_value):
			# It's a valid SA ID
			frappe.db.set_value(
				"GLP-1 Intake Submission",
				sub.name,
				"sa_id_number",
				id_value,
				update_modified=False
			)
			migrated_sa_id += 1
		else:
			# Treat as passport
			frappe.db.set_value(
				"GLP-1 Intake Submission",
				sub.name,
				"passport_number",
				id_value,
				update_modified=False
			)
			migrated_passport += 1
	
	# Migrate GLP-1 Intake Form records (child table)
	try:
		forms = frappe.db.sql("""
			SELECT name, id_number
			FROM `tabGLP-1 Intake Form`
			WHERE id_number IS NOT NULL
			AND id_number != ''
			AND (sa_id_number IS NULL OR sa_id_number = '')
			AND (passport_number IS NULL OR passport_number = '')
		""", as_dict=True)
	except Exception:
		forms = []
	
	for form in forms:
		id_value = form.id_number.strip()
		
		if is_valid_sa_id(id_value):
			frappe.db.set_value(
				"GLP-1 Intake Form",
				form.name,
				"sa_id_number",
				id_value,
				update_modified=False
			)
		else:
			frappe.db.set_value(
				"GLP-1 Intake Form",
				form.name,
				"passport_number",
				id_value,
				update_modified=False
			)
	
	# Migrate Patient uid field to custom_sa_id_number
	try:
		patients = frappe.db.sql("""
			SELECT name, uid
			FROM `tabPatient`
			WHERE uid IS NOT NULL
			AND uid != ''
			AND (custom_sa_id_number IS NULL OR custom_sa_id_number = '')
			AND (custom_passport_number IS NULL OR custom_passport_number = '')
		""", as_dict=True)
	except Exception:
		patients = []
	
	for patient in patients:
		if patient.uid:
			id_value = patient.uid.strip()
			
			if is_valid_sa_id(id_value):
				frappe.db.set_value(
					"Patient",
					patient.name,
					"custom_sa_id_number",
					id_value,
					update_modified=False
				)
			else:
				frappe.db.set_value(
					"Patient",
					patient.name,
					"custom_passport_number",
					id_value,
					update_modified=False
				)
	
	frappe.db.commit()
	
	print(f"Migration complete:")
	print(f"  - GLP-1 Intake Submission: {migrated_sa_id} SA IDs, {migrated_passport} Passports")
	print(f"  - GLP-1 Intake Form: {len(forms)} records migrated")
	print(f"  - Patient: {len(patients)} records migrated")
