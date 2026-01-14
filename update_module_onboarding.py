#!/usr/bin/env python3
"""
Script to update Module Onboarding records in the database
to replace ERPNext with KoraFlow in user-facing text.
"""

import frappe

def update_module_onboarding():
	"""Update Module Onboarding records to replace ERPNext with KoraFlow"""
	
	# Find the "Home" Module Onboarding record
	onboarding_name = "Home"
	
	if not frappe.db.exists("Module Onboarding", onboarding_name):
		print(f"Module Onboarding '{onboarding_name}' not found in database")
		return
	
	doc = frappe.get_doc("Module Onboarding", onboarding_name)
	
	# Update title
	if doc.title and "ERPNext" in doc.title:
		old_title = doc.title
		doc.title = doc.title.replace("ERPNext", "KoraFlow")
		print(f"Updated title: '{old_title}' -> '{doc.title}'")
	
	# Update success_message
	if doc.success_message and "ERPNext" in doc.success_message:
		old_msg = doc.success_message
		doc.success_message = doc.success_message.replace("ERPNext", "KoraFlow")
		print(f"Updated success_message: '{old_msg}' -> '{doc.success_message}'")
	
	# Update subtitle if needed
	if doc.subtitle and "ERPNext" in doc.subtitle:
		old_subtitle = doc.subtitle
		doc.subtitle = doc.subtitle.replace("ERPNext", "KoraFlow")
		print(f"Updated subtitle: '{old_subtitle}' -> '{doc.subtitle}'")
	
	# Save the document
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	
	print(f"Successfully updated Module Onboarding '{onboarding_name}'")
	
	# Also check and update any other Module Onboarding records
	all_onboardings = frappe.get_all("Module Onboarding", fields=["name", "title", "success_message", "subtitle"])
	
	updated_count = 0
	for ob in all_onboardings:
		if ob.name == onboarding_name:
			continue  # Already updated
		
		needs_update = False
		doc = frappe.get_doc("Module Onboarding", ob.name)
		
		if doc.title and "ERPNext" in doc.title:
			doc.title = doc.title.replace("ERPNext", "KoraFlow")
			needs_update = True
		
		if doc.success_message and "ERPNext" in doc.success_message:
			doc.success_message = doc.success_message.replace("ERPNext", "KoraFlow")
			needs_update = True
		
		if doc.subtitle and "ERPNext" in doc.subtitle:
			doc.subtitle = doc.subtitle.replace("ERPNext", "KoraFlow")
			needs_update = True
		
		if needs_update:
			doc.save(ignore_permissions=True)
			updated_count += 1
			print(f"Updated Module Onboarding '{ob.name}'")
	
	if updated_count > 0:
		frappe.db.commit()
		print(f"Updated {updated_count} additional Module Onboarding records")
	
	print("Module Onboarding update complete!")

if __name__ == "__main__":
	# This script should be run via bench console
	# bench --site <site-name> console
	# Then: exec(open('update_module_onboarding.py').read())
	update_module_onboarding()

