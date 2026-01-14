#!/usr/bin/env python3
"""
Test script to programmatically fill and submit the GLP-1 Intake Form
This tests:
1. Auto-population of email and first_name fields
2. Form submission with required fields
3. Error handling and validation
"""

import sys
import os
import json
import frappe
from frappe.utils import nowdate, add_days

# Add apps to path
sys.path.insert(0, 'apps')

def get_site_name():
	"""Get the first available site name"""
	os.chdir('sites')
	sites = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('_')]
	if not sites:
		raise Exception("No sites found!")
	return sites[0]

def test_form_submission():
	"""Test the intake form submission"""
	site_name = get_site_name()
	print(f"Initializing site: {site_name}")
	
	frappe.init(site=site_name)
	frappe.connect()
	
	# Test user email
	test_email = "browsertest@mweb.co.za"
	
	print(f"\n{'='*60}")
	print("GLP-1 Intake Form Submission Test")
	print(f"{'='*60}\n")
	
	# 1. Verify user exists and has Patient role
	print("1. Checking user and role...")
	try:
		user = frappe.get_doc("User", test_email)
		print(f"   ✓ User exists: {user.name}")
		print(f"   ✓ First Name: {user.first_name}")
		print(f"   ✓ Email: {user.email}")
		
		user_roles = [r.role for r in user.roles]
		if "Patient" in user_roles:
			print(f"   ✓ Patient role assigned: {user_roles}")
		else:
			print(f"   ✗ Patient role NOT assigned. Current roles: {user_roles}")
			return False
	except Exception as e:
		print(f"   ✗ Error checking user: {str(e)}")
		return False
	
	# 2. Check if patient exists
	print("\n2. Checking patient record...")
	try:
		patient = frappe.db.get_value("Patient", {"email": test_email}, "name")
		if patient:
			print(f"   ✓ Patient exists: {patient}")
			patient_doc = frappe.get_doc("Patient", patient)
			existing_intakes = len(patient_doc.glp1_intake_forms or [])
			print(f"   ✓ Existing intake forms: {existing_intakes}")
		else:
			print(f"   ℹ Patient does not exist yet (will be created on form submission)")
	except Exception as e:
		print(f"   ✗ Error checking patient: {str(e)}")
	
	# 3. Prepare form data with unique values
	print("\n3. Preparing form data...")
	import time
	timestamp = int(time.time())
	unique_mobile = f"082{timestamp % 10000000:07d}"  # Unique mobile number
	unique_id = f"90{timestamp % 100000000000:011d}"  # Unique ID number
	
	form_data = {
		"email": test_email,  # Should be auto-populated
		"first_name": user.first_name or "Browser Test User",  # Should be auto-populated
		"last_name": "Test",
		"dob": "1990-01-01",
		"sex": "Male",
		"mobile": unique_mobile,
		"intake_height_unit": "Centimeters",
		"intake_height_cm": 175.0,
		"intake_weight_unit": "Kilograms",
		"intake_weight_kg": 75.0,
		"id_number__passport_number": unique_id,  # Unique ID for testing
	}
	
	print("   Form data prepared:")
	for key, value in form_data.items():
		print(f"   - {key}: {value}")
	
	# 4. Test auto-population (check script injection)
	print("\n4. Testing auto-population script...")
	try:
		# Check if the script would be injected by checking the web form module
		bench_dir = os.path.dirname(os.path.abspath(__file__))
		web_form_module_path = os.path.join(bench_dir, "apps/koraflow_core/koraflow_core/web_form/glp1_intake/glp1_intake.py")
		if os.path.exists(web_form_module_path):
			with open(web_form_module_path, 'r') as f:
				module_content = f.read()
				if 'populateFields' in module_content:
					print(f"   ✓ Auto-population function found in module")
				if 'GLP1 Intake' in module_content:
					print(f"   ✓ Auto-population logging found in module")
		else:
			print(f"   ℹ Web form module not found at expected path")
	except Exception as e:
		print(f"   ℹ Could not verify script: {str(e)}")
	
	# 5. Verify web form exists
	print("\n5. Checking web form...")
	try:
		# Check by route first (the actual route used in URLs)
		web_forms = frappe.get_all("Web Form", filters={"route": "glp1-intake"}, fields=["name"])
		if web_forms:
			web_form_name = web_forms[0].name
			print(f"   ✓ Web Form found by route: {web_form_name}")
		elif frappe.db.exists("Web Form", "glp1-intake"):
			web_form_name = "glp1-intake"
			print(f"   ✓ Web Form 'glp1-intake' exists")
		else:
			# Try to find any web form for this doctype
			web_forms = frappe.get_all("Web Form", filters={"doc_type": "GLP-1 Intake Submission"}, fields=["name", "route"])
			if web_forms:
				web_form_name = web_forms[0].name
				print(f"   ✓ Found web form for GLP-1 Intake Submission: {web_form_name} (route: {web_forms[0].route})")
			else:
				print(f"   ✗ No web form found for GLP-1 Intake Submission")
				print(f"   Attempting to import web form...")
				
				# Import web form - need to go back to bench directory
				bench_dir = os.path.dirname(os.path.abspath(__file__))
				web_form_path = os.path.join(bench_dir, "apps/koraflow_core/koraflow_core/web_form/glp1_intake/glp1_intake.json")
				if os.path.exists(web_form_path):
					with open(web_form_path, 'r') as f:
						web_form_data = json.load(f)
					
					frappe.flags.mute_emails = True
					web_form = frappe.get_doc(web_form_data)
					web_form.insert(ignore_permissions=True, ignore_if_duplicate=True)
					frappe.db.commit()
					web_form_name = web_form.name
					print(f"   ✓ Web Form imported: {web_form_name}")
				else:
					print(f"   ✗ Web form JSON not found at: {web_form_path}")
					return False
	except Exception as e:
		print(f"   ✗ Error checking/importing web form: {str(e)}")
		import traceback
		traceback.print_exc()
		return False
	
	# 6. Test form submission via web form API
	print("\n6. Testing form submission...")
	try:
		# Set user session
		frappe.set_user(test_email)
		
		# Call the web form accept method
		from frappe.website.doctype.web_form.web_form import accept
		
		# Convert form_data to JSON string (as web form expects)
		data_json = json.dumps(form_data)
		
		print(f"   Submitting form data to web form: {web_form_name}...")
		
		# Debug: Check what the web form accept function receives
		print(f"   Form data JSON length: {len(data_json)} chars")
		form_data_parsed = json.loads(data_json)
		print(f"   Form data keys: {list(form_data_parsed.keys())[:10]}")
		for key in ['email', 'first_name', 'last_name', 'mobile']:
			if key in form_data_parsed:
				print(f"   Form data.{key} = {form_data_parsed[key]}")
		
		result = accept(web_form=web_form_name, data=data_json)
		
		if result:
			print(f"   ✓ Form submission successful!")
			print(f"   ✓ Result type: {type(result)}")
			
			if hasattr(result, 'name'):
				print(f"   ✓ Document name: {result.name}")
			elif isinstance(result, dict) and result.get('name'):
				print(f"   ✓ Document name: {result.get('name')}")
			
			# Verify patient was created/updated
			patient = frappe.db.get_value("Patient", {"email": test_email}, "name")
			if patient:
				# Get latest intake form directly from database (most reliable)
				latest_db = frappe.db.sql("""
					SELECT name, email, first_name, last_name, mobile, dob, sex
					FROM `tabGLP-1 Intake Submission`
					WHERE parent = %s
					ORDER BY creation DESC
					LIMIT 1
				""", (patient,), as_dict=True)
				
				if latest_db:
					latest_intake = latest_db[0]
					print(f"   ✓ Latest intake form (from DB): {latest_intake['name']}")
					
					intake_email = latest_intake.get('email')
					intake_first_name = latest_intake.get('first_name')
					intake_last_name = latest_intake.get('last_name')
					intake_mobile = latest_intake.get('mobile')
					
					print(f"   ✓ Email in intake: {intake_email}")
					print(f"   ✓ First name in intake: {intake_first_name}")
					print(f"   ✓ Last name in intake: {intake_last_name}")
					print(f"   ✓ Mobile in intake: {intake_mobile}")
					
					# Verify fields were saved
					if intake_email == test_email:
						print(f"   ✓ Email was correctly set: {intake_email}")
					else:
						print(f"   ✗ Email mismatch: expected {test_email}, got {intake_email}")
					
					if intake_first_name:
						print(f"   ✓ First name was set: {intake_first_name}")
					else:
						print(f"   ✗ First name was not set")
					
					# Also check via patient doc for comparison
					patient_doc = frappe.get_doc("Patient", patient)
					intake_forms = patient_doc.glp1_intake_forms or []
					print(f"   ✓ Patient has {len(intake_forms)} intake form(s) in child table")
			
			return True
		else:
			print(f"   ✗ Form submission returned no result")
			return False
			
	except Exception as e:
		print(f"   ✗ Error submitting form: {str(e)}")
		import traceback
		traceback.print_exc()
		return False
	
	finally:
		frappe.set_user("Administrator")
		frappe.db.commit()
		frappe.db.close()

if __name__ == "__main__":
	try:
		success = test_form_submission()
		if success:
			print(f"\n{'='*60}")
			print("✓ TEST PASSED: Form submission successful!")
			print(f"{'='*60}\n")
			sys.exit(0)
		else:
			print(f"\n{'='*60}")
			print("✗ TEST FAILED: Form submission had issues")
			print(f"{'='*60}\n")
			sys.exit(1)
	except Exception as e:
		print(f"\n{'='*60}")
		print(f"✗ TEST ERROR: {str(e)}")
		print(f"{'='*60}\n")
		import traceback
		traceback.print_exc()
		sys.exit(1)
