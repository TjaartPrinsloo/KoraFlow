"""
Courier Guy API Client
Handles all API interactions with The Courier Guy
"""
import frappe
import requests
import json
from typing import Dict, Optional, Any


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
	
	def create_waybill(self, waybill_doc) -> Dict:
		"""
		Create a waybill in Courier Guy system
		
		Args:
			waybill_doc: Courier Guy Waybill document
		
		Returns:
			Response dictionary with waybill_number and tracking_number
		"""
		# Prepare waybill data
		waybill_data = {
			"service_type": waybill_doc.service_type or self.settings.default_service_type,
			"parcel_count": waybill_doc.parcel_count or 1,
			"total_weight": waybill_doc.total_weight or 1.0,
			"total_value": float(waybill_doc.total_value or 0),
			"insurance_required": bool(waybill_doc.insurance_required),
			"signature_required": bool(waybill_doc.signature_required),
			"special_instructions": waybill_doc.special_instructions or "",
			
			# Pickup details
			"pickup": {
				"name": waybill_doc.pickup_name,
				"address": waybill_doc.pickup_address,
				"suburb": waybill_doc.pickup_suburb,
				"city": waybill_doc.pickup_city,
				"postal_code": waybill_doc.pickup_postal_code,
				"country": waybill_doc.pickup_country or "South Africa",
				"contact_name": waybill_doc.pickup_contact_name,
				"contact_phone": waybill_doc.pickup_contact_phone,
				"contact_email": waybill_doc.pickup_contact_email
			},
			
			# Delivery details
			"delivery": {
				"name": waybill_doc.delivery_name,
				"address": waybill_doc.delivery_address,
				"suburb": waybill_doc.delivery_suburb,
				"city": waybill_doc.delivery_city,
				"postal_code": waybill_doc.delivery_postal_code,
				"country": waybill_doc.delivery_country or "South Africa",
				"contact_name": waybill_doc.delivery_contact_name,
				"contact_phone": waybill_doc.delivery_contact_phone,
				"contact_email": waybill_doc.delivery_contact_email
			},
			
			# Reference
			"reference": waybill_doc.delivery_note,
			"test_mode": self.test_mode
		}
		
		# Note: Shiplogic v2 uses /v2/shipments
		response = self._make_request("POST", "/v2/shipments", waybill_data)
		
		if response.get("success"):
			data = response.get("data", {})
			
			# Extract waybill and tracking numbers
			# Adjust field names based on actual API response
			return {
				"success": True,
				"waybill_number": data.get("waybill_number") or data.get("waybill_no") or data.get("id"),
				"tracking_number": data.get("tracking_number") or data.get("tracking_no") or data.get("consignment_number"),
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
		response = self._make_request("GET", f"/v2/tracking/{tracking_number}")
		
		if response.get("success"):
			data = response.get("data", {})
			
			return {
				"success": True,
				"status": data.get("status", ""),
				"history": data.get("history", data.get("tracking_history", [])),
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
		response = self._make_request("GET", f"/v2/shipments/{waybill_number}/label")
		
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
		response = self._make_request("POST", f"/v2/shipments/cancel", {
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
				
		# Shiplogic v2 endpoint
		response = self._make_request("GET", "/v2/shipments", params)
		
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
		response = self._make_request("GET", "/v2/shipments", params)
		
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
			"shipments": shipments[:100], # Return top 100 for display
			"source": "api"
		}

