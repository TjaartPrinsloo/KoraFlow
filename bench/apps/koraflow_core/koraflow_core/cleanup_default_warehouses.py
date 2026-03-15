# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Remove default ERPNext warehouses that are not needed for healthcare dispensing
Only removes warehouses with no transactions or stock
"""

import frappe
from frappe import _


def cleanup_default_warehouses():
	"""Remove default ERPNext warehouses if they're not in use"""
	
	default_warehouses = [
		"Goods In Transit - S2W",
		"Finished Goods - S2W",
		"Work In Progress - S2W",
		"Stores - S2W"
	]
	
	# Keep "All Warehouses - S2W" as it's typically a parent warehouse
	
	removed = []
	skipped = []
	
	for wh_name in default_warehouses:
		if not frappe.db.exists("Warehouse", wh_name):
			continue
		
		wh = frappe.get_doc("Warehouse", wh_name)
		
		# Check for usage
		stock_entries = frappe.db.count("Stock Entry", {"from_warehouse": wh_name}) + \
		               frappe.db.count("Stock Entry", {"to_warehouse": wh_name})
		
		ledger_entries = frappe.db.count("Stock Ledger Entry", {"warehouse": wh_name})
		
		# Check for actual stock
		bins = frappe.get_all("Bin", filters={"warehouse": wh_name}, fields=["sum(actual_qty) as total_qty"])
		total_qty = bins[0].total_qty if bins and bins[0].total_qty else 0
		
		# Check for child warehouses
		child_warehouses = frappe.get_all("Warehouse", filters={"parent_warehouse": wh_name}, fields=["name"])
		
		if stock_entries == 0 and ledger_entries == 0 and total_qty == 0 and len(child_warehouses) == 0:
			# Safe to remove
			try:
				# Delete associated bins first
				frappe.db.delete("Bin", {"warehouse": wh_name})
				
				# Delete the warehouse
				frappe.delete_doc("Warehouse", wh_name, force=1, ignore_permissions=True)
				removed.append(wh_name)
				frappe.msgprint(_("Removed warehouse: {0}").format(wh_name))
			except Exception as e:
				frappe.log_error(title="Warehouse Cleanup", message=f"Could not remove warehouse {wh_name}: {str(e)}")
				skipped.append(f"{wh_name} (error: {str(e)})")
		else:
			# Has usage, skip
			reasons = []
			if stock_entries > 0:
				reasons.append(f"{stock_entries} stock entries")
			if ledger_entries > 0:
				reasons.append(f"{ledger_entries} ledger entries")
			if total_qty > 0:
				reasons.append(f"{total_qty} units in stock")
			if len(child_warehouses) > 0:
				reasons.append(f"{len(child_warehouses)} child warehouses")
			
			skipped.append(f"{wh_name} (has: {', '.join(reasons)})")
	
	frappe.db.commit()
	
	print("\n" + "="*60)
	print("WAREHOUSE CLEANUP COMPLETE")
	print("="*60)
	print(f"\n✅ Removed: {len(removed)}")
	for wh in removed:
		print(f"   - {wh}")
	
	if skipped:
		print(f"\n⚠️  Skipped: {len(skipped)}")
		for wh in skipped:
			print(f"   - {wh}")
	
	print("\n" + "="*60)


if __name__ == "__main__":
	cleanup_default_warehouses()
