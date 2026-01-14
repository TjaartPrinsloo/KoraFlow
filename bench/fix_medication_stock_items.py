#!/usr/bin/env python3
"""
Fix medication items to ensure they have is_stock_item flag set.
This script updates all items linked to medications to ensure they work with the stock module.
"""

import frappe

def fix_medication_stock_items():
	"""Update all items linked to medications to set is_stock_item = 1"""
	
	# Get all medication linked items
	medication_items = frappe.get_all(
		"Medication Linked Item",
		fields=["item", "item_code", "parent"],
		filters={"item": ["!=", ""]}
	)
	
	updated_count = 0
	skipped_count = 0
	error_count = 0
	
	print(f"Found {len(medication_items)} medication linked items to check...")
	
	for med_item in medication_items:
		item_code = med_item.get("item") or med_item.get("item_code")
		if not item_code:
			skipped_count += 1
			continue
			
		try:
			if frappe.db.exists("Item", item_code):
				item_doc = frappe.get_doc("Item", item_code)
				
				# Check if item needs to be updated
				if not item_doc.is_stock_item:
					item_doc.is_stock_item = 1
					item_doc.save(ignore_permissions=True)
					updated_count += 1
					print(f"✓ Updated {item_code} (from Medication: {med_item.parent})")
				else:
					skipped_count += 1
			else:
				print(f"⚠ Item {item_code} not found (from Medication: {med_item.parent})")
				error_count += 1
		except Exception as e:
			print(f"✗ Error updating {item_code}: {str(e)}")
			error_count += 1
	
	print("\n" + "="*60)
	print("Summary:")
	print(f"  Updated: {updated_count} items")
	print(f"  Already correct: {skipped_count} items")
	print(f"  Errors: {error_count} items")
	print("="*60)
	
	return {
		"updated": updated_count,
		"skipped": skipped_count,
		"errors": error_count
	}

if __name__ == "__main__":
	frappe.init(site="koraflow-site")
	frappe.connect()
	
	try:
		results = fix_medication_stock_items()
		print("\n✓ Script completed successfully!")
	except Exception as e:
		print(f"\n✗ Script failed: {str(e)}")
		import traceback
		traceback.print_exc()
	finally:
		frappe.destroy()
