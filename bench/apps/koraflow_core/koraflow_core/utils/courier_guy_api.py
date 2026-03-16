"""
Courier Guy API Client
Handles all API interactions with The Courier Guy (via Shiplogic API)
"""
import frappe
import requests
import json
from typing import Dict, Optional, Any, List


# Map human-readable service types to TCG service level codes
# TCG uses different codes for local vs national routes:
#   Local: LOF (Overnight), LSF (Same Day Flyer), LSE (Same Day Economy), LOX (Overnight Parcel), SDX (Express)
#   National: ECO (Economy), OVN (Overnight), SDX (Express)
# We map each Settings option to multiple possible codes, ordered by preference
SERVICE_LEVEL_PREFERENCES = {
	"Economy": ["ECO", "LSE", "LOF"],         # Cheapest options
	"Express": ["SDX"],                        # Same Day Express
	"Next Day": ["OVN", "LOF", "LOX"],         # Overnight/Next Day options
	"Same Day": ["LSF", "LSE", "SDX"],         # Same Day options
}


class CourierGuyAPI:
	"""Client for Courier Guy API"""

	def __init__(self):
		"""Initialize API client with settings"""
		self.settings = frappe.get_single("Courier Guy Settings")

		if not self.settings.enabled:
			raise Exception("Courier Guy integration is not enabled")

		self.api_key = self.settings.get_password("api_key")
		self.api_url = self.settings.api_url.rstrip("/")
		self.test_mode = self.settings.test_mode

		# Set base headers
		self.headers = {
			"Content-Type": "application/json",
			"Accept": "application/json",
			"Authorization": f"Bearer {self.api_key}",
			"X-API-Key": self.api_key
		}

	def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
		"""
		Make API request to Courier Guy

		Args:
			method: HTTP method (GET, POST, etc.)
			endpoint: API endpoint (without base URL)
			data: Request payload

		Returns:
			Response dictionary
		"""
		url = f"{self.api_url}/{endpoint.lstrip('/')}"

		try:
			frappe.logger().info(f"Courier Guy API Debug: URL {method} {url}, Params/Data: {data}")
			if method.upper() == "GET":
				response = requests.get(url, headers=self.headers, params=data, timeout=30)
			elif method.upper() == "POST":
				response = requests.post(url, headers=self.headers, json=data, timeout=30)
			else:
				raise ValueError(f"Unsupported HTTP method: {method}")
			frappe.logger().info(f"Courier Guy API Debug: Status {response.status_code}, Response: {response.text[:500]}")
			response.raise_for_status()

			# Try to parse JSON response
			try:
				return {
					"success": True,
					"data": response.json(),
					"status_code": response.status_code
				}
			except ValueError:
				# If not JSON, return text
				return {
					"success": True,
					"data": response.text,
					"status_code": response.status_code
				}

		except requests.exceptions.RequestException as e:
			# Truncate error message for the log title if needed
			error_msg = str(e)
			log_title = f"Courier Guy API Error: {error_msg[:100]}"
			frappe.log_error(title=log_title, message=error_msg)
			return {
				"success": False,
				"error": error_msg,
				"status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
			}

	# =====================
	# Address Helpers
	# =====================

	def build_collection_address_from_settings(self) -> Dict:
		"""Build TCG-format collection address from Courier Guy Settings"""
		return {
			"type": "business",
			"company": self.settings.pickup_contact_name or "",
			"street_address": self.settings.default_pickup_address or "",
			"local_area": self.settings.pickup_local_area or self.settings.pickup_suburb or "",
			"city": self.settings.pickup_city or "",
			"zone": self.settings.pickup_zone or "",
			"country": "ZA",
			"code": self.settings.pickup_postal_code or ""
		}

	def build_delivery_address_from_patient(self, patient_name: str) -> Optional[Dict]:
		"""
		Build TCG-format delivery address from Patient's linked Address record.
		Falls back to Patient custom fields if no Address record found.
		"""
		# Try to find linked Address via Dynamic Link
		address_names = frappe.get_all("Dynamic Link", filters={
			"link_doctype": "Patient",
			"link_name": patient_name,
			"parenttype": "Address"
		}, pluck="parent")

		if address_names:
			address = frappe.get_doc("Address", address_names[0])
			return {
				"type": "residential",
				"company": "",
				"street_address": address.address_line1 or "",
				"local_area": address.city or "",
				"city": address.city or "",
				"zone": address.state or "",
				"country": "ZA",
				"code": address.pincode or ""
			}

		# Fallback to Patient custom fields
		patient = frappe.get_doc("Patient", patient_name)
		address_line = patient.address_line1 if hasattr(patient, 'address_line1') and patient.address_line1 else getattr(patient, 'custom_address_line1', '')
		city = patient.city if hasattr(patient, 'city') and patient.city else getattr(patient, 'custom_city', '')
		state = patient.state if hasattr(patient, 'state') and patient.state else getattr(patient, 'custom_state', '')
		pincode = patient.zip_code if hasattr(patient, 'zip_code') and patient.zip_code else getattr(patient, 'custom_pincode', '')

		if not address_line and not city:
			return None

		return {
			"type": "residential",
			"company": "",
			"street_address": address_line or "",
			"local_area": city or "",
			"city": city or "",
			"zone": state or "",
			"country": "ZA",
			"code": pincode or ""
		}

	def build_delivery_address_from_address_doc(self, address_name: str) -> Dict:
		"""Build TCG-format delivery address from an ERPNext Address document"""
		address = frappe.get_doc("Address", address_name)
		return {
			"type": "residential",
			"company": address.address_title or "",
			"street_address": address.address_line1 or "",
			"local_area": address.city or "",
			"city": address.city or "",
			"zone": address.state or "",
			"country": "ZA",
			"code": address.pincode or ""
		}

	def _get_default_parcels(self) -> List[Dict]:
		"""Get default parcel dimensions from Settings"""
		return [{
			"submitted_length_cm": float(self.settings.default_parcel_length_cm or 20),
			"submitted_width_cm": float(self.settings.default_parcel_width_cm or 20),
			"submitted_height_cm": float(self.settings.default_parcel_height_cm or 10),
			"submitted_weight_kg": float(self.settings.default_parcel_weight_kg or 2)
		}]

	def _get_preferred_codes(self, service_type: Optional[str] = None) -> List[str]:
		"""Get preferred service level codes for a given service type"""
		service = service_type or self.settings.default_service_type or "Economy"
		return SERVICE_LEVEL_PREFERENCES.get(service, ["ECO", "LOF"])

	def _get_service_level_code(self, service_type: Optional[str] = None) -> str:
		"""Map human-readable service type to first preferred TCG service level code"""
		codes = self._get_preferred_codes(service_type)
		return codes[0] if codes else "ECO"

	# =====================
	# Rate Endpoints
	# =====================

	def get_rates(self, collection_address: Dict, delivery_address: Dict,
	              parcels: Optional[List[Dict]] = None, declared_value: float = 0) -> Dict:
		"""
		Get shipping rates from TCG API.

		Args:
			collection_address: TCG-format collection address
			delivery_address: TCG-format delivery address
			parcels: List of parcel dimensions. Uses defaults if not provided.
			declared_value: Declared value for insurance

		Returns:
			Dict with success, rates list, and selected_rate matching default service type
		"""
		if parcels is None:
			parcels = self._get_default_parcels()

		rate_data = {
			"collection_address": collection_address,
			"delivery_address": delivery_address,
			"parcels": parcels,
			"declared_value": declared_value
		}

		response = self._make_request("POST", "/rates", rate_data)

		if response.get("success"):
			data = response.get("data", {})
			rates = data if isinstance(data, list) else data.get("rates", [])

			# Find the rate matching default service type preference
			# TCG nests service level info under rate.service_level.code
			# TCG uses different codes for local vs national, so we check multiple preferred codes
			preferred_codes = self._get_preferred_codes()
			selected_rate = None

			# Build a code->rate lookup
			rate_by_code = {}
			for rate in rates:
				service_level = rate.get("service_level", {})
				code = service_level.get("code", "") or rate.get("service_level_code", "")
				rate_by_code[code] = rate

			# Pick the first matching preferred code
			for code in preferred_codes:
				if code in rate_by_code:
					selected_rate = rate_by_code[code]
					break

			# If no match, pick the cheapest available rate
			if not selected_rate and rates:
				selected_rate = min(rates, key=lambda r: r.get("rate", float("inf")))

			return {
				"success": True,
				"rates": rates,
				"selected_rate": selected_rate,
				"raw_response": data
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_rates_for_patient(self, patient_name: str, declared_value: float = 0) -> Dict:
		"""
		Convenience method: Get rates for shipping to a patient.

		Args:
			patient_name: Patient document name
			declared_value: Declared value for insurance

		Returns:
			Dict with success, rates, selected_rate, and courier_fee (the rate amount)
		"""
		collection_address = self.build_collection_address_from_settings()
		delivery_address = self.build_delivery_address_from_patient(patient_name)

		if not delivery_address:
			return {
				"success": False,
				"error": f"No address found for patient {patient_name}",
				"courier_fee": self.settings.default_rate or 99.00
			}

		result = self.get_rates(collection_address, delivery_address, declared_value=declared_value)

		if result.get("success") and result.get("selected_rate"):
			selected = result["selected_rate"]
			result["courier_fee"] = selected.get("rate", 0)
			service_level = selected.get("service_level", {})
			result["service_level_code"] = service_level.get("code", "")
			result["service_level_name"] = service_level.get("name", "")
		else:
			result["courier_fee"] = self.settings.default_rate or 99.00

		return result

	# =====================
	# Shipment Endpoints
	# =====================

	def create_waybill(self, waybill_doc) -> Dict:
		"""
		Create a shipment in Courier Guy system.

		Uses the TCG Shiplogic API format: POST /shipments

		Args:
			waybill_doc: Courier Guy Waybill document

		Returns:
			Response dictionary with waybill_number and tracking_number
		"""
		# Map country name to ISO code
		def country_code(country_name):
			if country_name and country_name.lower() in ("south africa", "za"):
				return "ZA"
			return country_name or "ZA"

		shipment_data = {
			"collection_address": {
				"type": "business",
				"company": waybill_doc.pickup_name or "",
				"street_address": waybill_doc.pickup_address or "",
				"local_area": waybill_doc.pickup_suburb or "",
				"city": waybill_doc.pickup_city or "",
				"zone": self.settings.pickup_zone or "",
				"country": country_code(waybill_doc.pickup_country),
				"code": waybill_doc.pickup_postal_code or ""
			},
			"collection_contact": {
				"name": waybill_doc.pickup_contact_name or "",
				"mobile_number": waybill_doc.pickup_contact_phone or "",
				"email": waybill_doc.pickup_contact_email or ""
			},
			"delivery_address": {
				"type": "residential",
				"company": "",
				"street_address": waybill_doc.delivery_address or "",
				"local_area": waybill_doc.delivery_suburb or "",
				"city": waybill_doc.delivery_city or "",
				"zone": "",
				"country": country_code(waybill_doc.delivery_country),
				"code": waybill_doc.delivery_postal_code or ""
			},
			"delivery_contact": {
				"name": waybill_doc.delivery_contact_name or "",
				"mobile_number": waybill_doc.delivery_contact_phone or "",
				"email": waybill_doc.delivery_contact_email or ""
			},
			"parcels": [{
				"parcel_description": "Medication",
				"submitted_length_cm": float(self.settings.default_parcel_length_cm or 20),
				"submitted_width_cm": float(self.settings.default_parcel_width_cm or 20),
				"submitted_height_cm": float(self.settings.default_parcel_height_cm or 10),
				"submitted_weight_kg": float(waybill_doc.total_weight or self.settings.default_parcel_weight_kg or 2)
			}],
			"service_level_code": waybill_doc.service_level_code or self._get_service_level_code(waybill_doc.service_type),
			"declared_value": float(waybill_doc.total_value or 0),
			"customer_reference": waybill_doc.delivery_note or waybill_doc.name,
			"special_instructions_collection": "",
			"special_instructions_delivery": waybill_doc.special_instructions or "",
			"mute_notifications": False
		}

		response = self._make_request("POST", "/shipments", shipment_data)

		if response.get("success"):
			data = response.get("data", {})

			# Extract waybill and tracking numbers from response
			tracking_ref = (
				data.get("custom_tracking_reference")
				or data.get("tracking_reference")
				or data.get("waybill_number")
				or data.get("waybill_no")
				or data.get("short_tracking_reference")
			)
			shipment_id = data.get("id")

			return {
				"success": True,
				"waybill_number": tracking_ref or str(shipment_id or ""),
				"tracking_number": tracking_ref or str(shipment_id or ""),
				"shipment_id": shipment_id,
				"raw_response": data
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_tracking(self, tracking_number: str) -> Dict:
		"""
		Get tracking information for a waybill

		Args:
			tracking_number: Tracking number

		Returns:
			Tracking information dictionary
		"""
		response = self._make_request("GET", f"/tracking/{tracking_number}")

		if response.get("success"):
			data = response.get("data", {})

			return {
				"success": True,
				"status": data.get("status", ""),
				"history": data.get("history", data.get("tracking_history", data.get("tracking_events", []))),
				"current_location": data.get("current_location", ""),
				"estimated_delivery": data.get("estimated_delivery", ""),
				"raw_response": data
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_waybill_print(self, waybill_number: str) -> Dict:
		"""
		Get waybill print URL or PDF

		Args:
			waybill_number: Waybill number

		Returns:
			Print URL or PDF data
		"""
		response = self._make_request("GET", f"/shipments/{waybill_number}/label")

		if response.get("success"):
			data = response.get("data", {})

			return {
				"success": True,
				"print_url": data.get("print_url") or data.get("url"),
				"pdf_url": data.get("pdf_url") or data.get("pdf"),
				"pdf_data": data.get("pdf_data") or data.get("base64_pdf"),
				"raw_response": data
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def cancel_waybill(self, waybill_number: str, reason: str = "") -> Dict:
		"""
		Cancel a waybill

		Args:
			waybill_number: Waybill number
			reason: Cancellation reason

		Returns:
			Cancellation response
		"""
		response = self._make_request("POST", f"/shipments/cancel", {
			"tracking_reference": waybill_number,
			"reason": reason
		})

		if response.get("success"):
			return {
				"success": True,
				"message": "Waybill cancelled successfully",
				"raw_response": response.get("data", {})
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_shipments(self, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict:
		"""
		Fetch shipments from Courier Guy API

		Args:
			from_date: Start date (YYYY-MM-DD)
			to_date: End date (YYYY-MM-DD)
			limit: Number of records to fetch
			offset: Pagination offset

		Returns:
			Response with shipments list
		"""
		params: Dict[str, Any] = {
			"limit": limit,
			"offset": offset
		}

		if from_date:
			params["start_date"] = from_date
			params["date_filter"] = "time_created"

		if to_date:
			params["end_date"] = to_date
			if "date_filter" not in params:
				params["date_filter"] = "time_created"

		response = self._make_request("GET", "/shipments", params)

		if response.get("success"):
			data = response.get("data", {})
			shipments = data if isinstance(data, list) else data.get("shipments", [])
			return {
				"success": True,
				"shipments": shipments,
				"count": len(shipments),
				"raw_response": data
			}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_shipment_by_waybill(self, waybill_number: str) -> Dict:
		"""
		Fetch a specific shipment by waybill/tracking number
		"""
		params = {"tracking_reference": waybill_number}
		response = self._make_request("GET", "/shipments", params)

		if response.get("success"):
			data = response.get("data", {})
			shipments = data if isinstance(data, list) else data.get("shipments", [])
			if shipments:
				return {
					"success": True,
					"data": shipments[0],
					"raw_response": data
				}
			return {"success": False, "error": "Shipment not found"}
		else:
			return {
				"success": False,
				"error": response.get("error", "Unknown error"),
				"raw_response": response
			}

	def get_dashboard_data(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
		"""
		Get dashboard summary data.
		If no dedicated endpoint exists, we calculate it from shipments.
		"""
		# First try to get shipments
		res = self.get_shipments(from_date=from_date, to_date=to_date, limit=1000)
		if not res.get("success"):
			return res

		shipments = res.get("shipments", [])

		# Basic aggregation for dashboard
		summary = {
			"created": len(shipments),
			"collected": 0,
			"delivered": 0,
			"in_transit": 0,
			"failed": 0
		}

		for s in shipments:
			status = (s.get("status") or "").lower()
			if status == "delivered":
				summary["delivered"] += 1
			elif status in ["collected", "at-hub", "in-transit", "out-for-delivery"]:
				summary["collected"] += 1
				summary["in_transit"] += 1
			elif status in ["cancelled", "failed", "undeliverable"]:
				summary["failed"] += 1

		return {
			"success": True,
			"summary": summary,
			"shipments": shipments[:100],  # Return top 100 for display
			"source": "api"
		}
