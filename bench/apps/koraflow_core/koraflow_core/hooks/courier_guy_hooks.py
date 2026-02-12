"""
Courier Guy Hooks
Hooks for integrating Courier Guy with Delivery Notes
"""
import frappe
from koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill import create_waybill_from_delivery_note


def create_waybill_on_delivery_note_submit(doc, method):
	"""
	Automatically create waybill when Delivery Note is submitted
	"""
	# Check if Courier Guy is enabled
	try:
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return
	except:
		# Settings not configured, skip
		return
	
	# Check if waybill already exists
	existing_waybill = frappe.db.exists("Courier Guy Waybill", {"delivery_note": doc.name})
	if existing_waybill:
		return
	
	# Check if auto-create is enabled (you can add this setting later)
	# For now, we'll create it automatically
	
	try:
		# Create waybill
		waybill_name = create_waybill_from_delivery_note(doc.name)
		
		# Link waybill to delivery note
		frappe.db.set_value("Delivery Note", doc.name, "courier_guy_waybill", waybill_name)
		frappe.db.commit()
		
		frappe.msgprint(f"Courier Guy waybill created: {waybill_name}")
		
	except Exception as e:
		frappe.log_error(f"Error creating Courier Guy waybill: {str(e)}", "Courier Guy Integration")
		# Don't fail the delivery note submission if waybill creation fails
		frappe.msgprint(f"Warning: Could not create Courier Guy waybill: {str(e)}", indicator="orange")

