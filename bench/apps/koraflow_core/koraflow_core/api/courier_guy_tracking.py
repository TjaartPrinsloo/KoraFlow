"""
Courier Guy Tracking API
API endpoints for patient tracking and waybill management
"""
import frappe
from frappe import _
from koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill import CourierGuyWaybill


@frappe.whitelist(allow_guest=True)
def get_tracking_by_number(tracking_number):
	"""
	Get tracking information by tracking number
	Public endpoint for patient tracking
	
	Args:
		tracking_number: Courier Guy tracking number
	
	Returns:
		Tracking information
	"""
	if not tracking_number:
		frappe.throw("Tracking number is required")
	
	# Find waybill by tracking number
	waybill = frappe.db.get_value(
		"Courier Guy Waybill",
		{"tracking_number": tracking_number},
		["name", "status", "delivery_note", "patient", "customer"],
		as_dict=True
	)
	
	if not waybill:
		frappe.throw("Waybill not found for this tracking number")
	
	# Get waybill document
	waybill_doc = frappe.get_doc("Courier Guy Waybill", waybill.name)
	
	# Update tracking if needed
	try:
		waybill_doc.update_tracking()
	except:
		# If update fails, continue with existing data
		pass
	
	# Reload to get updated data
	waybill_doc.reload()
	
	# Parse tracking history
	tracking_history = []
	if waybill_doc.tracking_history:
		import json
		try:
			tracking_history = json.loads(waybill_doc.tracking_history)
		except:
			pass
	
	return {
		"success": True,
		"tracking_number": waybill_doc.tracking_number,
		"waybill_number": waybill_doc.waybill_number,
		"status": waybill_doc.status,
		"delivery_note": waybill_doc.delivery_note,
		"patient": waybill_doc.patient,
		"customer": waybill_doc.customer,
		"tracking_history": tracking_history,
		"last_update": waybill_doc.last_tracking_update,
		"delivery_address": {
			"name": waybill_doc.delivery_name,
			"address": waybill_doc.delivery_address,
			"suburb": waybill_doc.delivery_suburb,
			"city": waybill_doc.delivery_city,
			"postal_code": waybill_doc.delivery_postal_code,
			"country": waybill_doc.delivery_country
		}
	}


@frappe.whitelist()
def get_patient_tracking(patient_name):
	"""
	Get all waybills for a patient
	
	Args:
		patient_name: Patient name
	
	Returns:
		List of waybills with tracking information
	"""
	if not patient_name:
		frappe.throw("Patient name is required")
	
	# Get all waybills for this patient
	waybills = frappe.get_all(
		"Courier Guy Waybill",
		filters={"patient": patient_name},
		fields=["name", "delivery_note", "status", "tracking_number", "waybill_number", 
				"creation", "last_tracking_update"],
		order_by="creation desc"
	)
	
	result = []
	for waybill in waybills:
		waybill_doc = frappe.get_doc("Courier Guy Waybill", waybill.name)
		
		# Parse tracking history
		tracking_history = []
		if waybill_doc.tracking_history:
			import json
			try:
				tracking_history = json.loads(waybill_doc.tracking_history)
			except:
				pass
		
		result.append({
			"name": waybill.name,
			"delivery_note": waybill.delivery_note,
			"status": waybill.status,
			"tracking_number": waybill.tracking_number,
			"waybill_number": waybill.waybill_number,
			"created": waybill.creation,
			"last_update": waybill.last_tracking_update,
			"tracking_history": tracking_history,
			"delivery_address": {
				"name": waybill_doc.delivery_name,
				"address": waybill_doc.delivery_address,
				"city": waybill_doc.delivery_city
			}
		})
	
	return {
		"success": True,
		"waybills": result
	}


@frappe.whitelist()
def get_delivery_note_tracking(delivery_note):
	"""
	Get waybill tracking for a delivery note
	
	Args:
		delivery_note: Delivery Note name
	
	Returns:
		Waybill tracking information
	"""
	if not delivery_note:
		frappe.throw("Delivery Note is required")
	
	waybill = frappe.db.get_value(
		"Courier Guy Waybill",
		{"delivery_note": delivery_note},
		"name"
	)
	
	if not waybill:
		return {
			"success": False,
			"message": "No waybill found for this delivery note"
		}
	
	waybill_doc = frappe.get_doc("Courier Guy Waybill", waybill)
	
	# Parse tracking history
	tracking_history = []
	if waybill_doc.tracking_history:
		import json
		try:
			tracking_history = json.loads(waybill_doc.tracking_history)
		except:
			pass
	
	return {
		"success": True,
		"waybill": waybill_doc.name,
		"tracking_number": waybill_doc.tracking_number,
		"waybill_number": waybill_doc.waybill_number,
		"status": waybill_doc.status,
		"tracking_history": tracking_history,
		"last_update": waybill_doc.last_tracking_update
	}

