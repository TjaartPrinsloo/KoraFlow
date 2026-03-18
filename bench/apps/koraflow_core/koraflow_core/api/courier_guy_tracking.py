"""
Courier Guy Tracking API
API endpoints for patient tracking and waybill management
"""
import frappe
from frappe import _
from koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill import CourierGuyWaybill


@frappe.whitelist()
def get_shipping_rate(postal_code, city=None, street_address=None):
	"""
	Calculate shipping rate for a given address.
	Used by the quote acceptance modal to recalculate when address changes.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login"), frappe.AuthenticationError)

	try:
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return {"success": False, "courier_fee": getattr(settings, 'default_rate', 0) or 99, "message": "Courier integration disabled"}

		from koraflow_core.utils.courier_guy_api import CourierGuyAPI
		api = CourierGuyAPI()

		collection_address = api.build_collection_address_from_settings()

		# If no street address provided, try to get from patient's linked address
		if not street_address:
			patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
			if patient_name:
				addr = api.build_delivery_address_from_patient(patient_name)
				if addr:
					# Override postal code and city with provided values
					addr["code"] = postal_code or addr.get("code", "")
					if city:
						addr["city"] = city
						addr["local_area"] = city
					result = api.get_rates(collection_address, addr)
					if result.get("success") and result.get("selected_rate"):
						selected = result["selected_rate"]
						return {
							"success": True,
							"courier_fee": selected.get("rate", 0),
							"service_level": selected.get("service_level", {}).get("code", ""),
							"service_name": selected.get("service_level", {}).get("name", ""),
						}

		# Build delivery address from provided data
		delivery_address = {
			"type": "residential",
			"street_address": street_address or "1 Main Road",
			"local_area": city or "",
			"city": city or "",
			"zone": "",
			"country": "ZA",
			"code": postal_code or ""
		}

		result = api.get_rates(collection_address, delivery_address)

		if result.get("success") and result.get("selected_rate"):
			selected = result["selected_rate"]
			return {
				"success": True,
				"courier_fee": selected.get("rate", 0),
				"service_level": selected.get("service_level", {}).get("code", ""),
				"service_name": selected.get("service_level", {}).get("name", ""),
			}
		else:
			return {
				"success": False,
				"courier_fee": getattr(settings, 'default_rate', 0) or 99,
				"message": result.get("error", result.get("raw_response", {}).get("message", "Could not calculate rate"))
			}
	except Exception as e:
		frappe.log_error(title="Shipping Rate Error", message=str(e))
		return {"success": False, "courier_fee": 99, "message": str(e)}


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

