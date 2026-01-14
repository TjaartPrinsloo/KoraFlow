"""
Courier Guy API Client
Handles all API interactions with The Courier Guy
"""
import frappe
import requests
import json
from typing import Dict, Optional


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
			if method.upper() == "GET":
				response = requests.get(url, headers=self.headers, params=data, timeout=30)
			elif method.upper() == "POST":
				response = requests.post(url, headers=self.headers, json=data, timeout=30)
			else:
				raise ValueError(f"Unsupported HTTP method: {method}")
			
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
			frappe.log_error(f"Courier Guy API Error: {str(e)}", "Courier Guy API")
			return {
				"success": False,
				"error": str(e),
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
		
		# Make API request
		# Note: Adjust endpoint based on actual Courier Guy API documentation
		response = self._make_request("POST", "/api/v1/waybills", waybill_data)
		
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
		response = self._make_request("GET", f"/api/v1/tracking/{tracking_number}")
		
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
		response = self._make_request("GET", f"/api/v1/waybills/{waybill_number}/print")
		
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
		response = self._make_request("POST", f"/api/v1/waybills/{waybill_number}/cancel", {
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

