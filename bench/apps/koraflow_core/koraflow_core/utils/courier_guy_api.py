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

	def get_shipments(self, from_date=None, to_date=None, limit=100, **kwargs) -> Dict:
		"""
		Get list of shipments/waybills from Courier Guy API
		
		Args:
			from_date: Start date (YYYY-MM-DD) - Note: Ship Logic API may not support date filtering via params
			to_date: End date (YYYY-MM-DD) - Filtering is done client-side if API doesn't support it
			limit: Maximum number of shipments to return
			**kwargs: Additional parameters (e.g., tracking_reference)
		
		Returns:
			List of shipments/waybills
		"""
		# Ship Logic API endpoint (confirmed working)
		# Note: Date filtering may not work via query params, so we'll fetch all and filter client-side
		params = {}
		# Add any extra arguments to params
		params.update(kwargs)
		
		# Ship Logic API specific date filtering
		if from_date:
			params["date_filter"] = "time_created"
			# Format as ISO 8601 with timezone if it's a date/datetime
			# Use datetime.date and datetime.datetime from the module imported at top level
			if hasattr(from_date, 'strftime'):
				params["start_date"] = from_date.strftime("%Y-%m-%d 00:00:00+02:00")
			else:
				# Assume string is already YYYY-MM-DD or similar
				params["start_date"] = f"{from_date} 00:00:00+02:00" if " " not in str(from_date) else from_date
				
		if to_date:
			params["date_filter"] = "time_created"
			if hasattr(to_date, 'strftime'):
				params["end_date"] = to_date.strftime("%Y-%m-%d 23:59:59+02:00")
			else:
				params["end_date"] = f"{to_date} 23:59:59+02:00" if " " not in str(to_date) else to_date
				
		if limit:
			params["limit"] = min(int(limit), 1000)
		


		# Try the /shipments endpoint first (confirmed working)
		try:
			response = self._make_request("GET", "/shipments", params)
			
			if response.get("success"):
				data = response.get("data", {})
				# Handle different response formats
				shipments = []
				if isinstance(data, list):
					shipments = data
				elif isinstance(data, dict):
					shipments = data.get("shipments") or data.get("waybills") or data.get("data") or data.get("results") or []
				
				# Handle date filtering
				import datetime
				filtered_shipments = []
				for shipment in shipments:
					created_at = shipment.get("created_at") or shipment.get("time_created")
					if created_at and (from_date or to_date):
						try:
							# Parse ISO: 2024-09-10T08:10:33.224915Z
							created_dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
							created_date = created_dt.date()
							
							from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d").date() if isinstance(from_date, str) else from_date
							to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d").date() if isinstance(to_date, str) else to_date
							
							if (not from_date_obj or created_date >= from_date_obj) and (not to_date_obj or created_date <= to_date_obj):
								filtered_shipments.append(shipment)
						except:
							filtered_shipments.append(shipment)
					else:
						filtered_shipments.append(shipment)
				shipments = filtered_shipments
				
				if limit and len(shipments) > limit:
					shipments = shipments[:limit]
				
				return {"success": True, "shipments": shipments}
		except Exception as e:
			frappe.logger().error(f"Courier Guy API list failed: {str(e)}")
		
		return {"success": False, "shipments": [], "error": "Failed to fetch shipments"}
	
	def get_shipment_by_id(self, shipment_id) -> Dict:
		"""
		Get full shipment details by shipment ID
		"""
		# Try multiple variations of the endpoint
		variations = [
			f"/shipments/{shipment_id}",
			f"/api/v1/shipments/{shipment_id}",
			f"/v1/shipments/{shipment_id}"
		]
		
		for endpoint in variations:
			try:
				response = self._make_request("GET", endpoint)
				if response.get("success"):
					data = response.get("data")
					# Some APIs return the object directly, others wrap it in a 'shipment' key
					if isinstance(data, dict):
						shipment = data.get("shipment") or data.get("data") or data
						if isinstance(shipment, dict) and (shipment.get("id") or shipment.get("waybill_number")):
							return {"success": True, "data": shipment}
			except:
				continue
				
		return {"success": False, "error": f"Failed to retrieve shipment {shipment_id}"}
		
	def get_shipment_by_waybill(self, waybill_number: str) -> Dict:
		"""
		Try to get full shipment details using waybill number directly
		"""
		# Some implementations use waybill as the key in /shipments/{waybill}
		variations = [
			f"/waybills/{waybill_number}",
			f"/shipments/{waybill_number}",
			f"/api/v1/waybills/{waybill_number}",
			f"/api/v1/shipments/{waybill_number}"
		]
		
		for endpoint in variations:
			try:
				response = self._make_request("GET", endpoint)
				if response.get("success"):
					data = response.get("data")
					if isinstance(data, dict):
						shipment = data.get("shipment") or data.get("waybill") or data
						if isinstance(shipment, dict) and (shipment.get("delivery_contact_name") or shipment.get("delivery_to")):
							return {"success": True, "data": shipment}
			except:
				continue
				
		# Fallback: search /shipments with tracking_reference param
		search_res = self.get_shipments(tracking_reference=waybill_number, limit=1)
		if search_res.get("success") and search_res.get("shipments"):
			return {"success": True, "data": search_res["shipments"][0]}
			
		return {"success": False, "error": "Could not find full shipment record"}
	
	def get_dashboard_data(self, from_date=None, to_date=None) -> Dict:
		"""
		Get comprehensive dashboard data from Courier Guy API
		Fetches historical shipments and calculates dashboard metrics
		
		Args:
			from_date: Start date (YYYY-MM-DD)
			to_date: End date (YYYY-MM-DD)
		
		Returns:
			Dashboard data dictionary with charts, stats, KPIs, and shipments
		"""
		# First, get all shipments in the date range
		shipments_response = self.get_shipments(from_date=from_date, to_date=to_date, limit=1000)
		shipments = shipments_response.get("shipments", [])
		
		if not shipments:
			return {}
		
		# Calculate summary statistics
		created_count = len(shipments)
		collected_count = len([s for s in shipments if s.get("status") in ["Collected", "In Transit", "Out for Delivery", "Delivered"]])
		delivered_count = len([s for s in shipments if s.get("status") == "Delivered"])
		
		# Calculate chart data (group by date)
		chart_data = {"labels": [], "created": [], "collected": [], "delivered": []}
		if from_date and to_date:
			current_date = datetime.strptime(from_date, "%Y-%m-%d").date() if isinstance(from_date, str) else from_date
			end_date = datetime.strptime(to_date, "%Y-%m-%d").date() if isinstance(to_date, str) else to_date
			
			while current_date <= end_date:
				date_str = current_date.strftime("%d/%m/%y")
				chart_data["labels"].append(date_str)
				
				# Count shipments for this date
				created = len([s for s in shipments 
					if (s.get("time_created") or s.get("created_at")) and 
					datetime.strptime((s.get("time_created") or s.get("created_at"))[:10], "%Y-%m-%d").date() == current_date])
				collected = len([s for s in shipments 
					if (s.get("collected_at") or s.get("collected_date")) and 
					datetime.strptime((s.get("collected_at") or s.get("collected_date"))[:10], "%Y-%m-%d").date() == current_date])
				delivered = len([s for s in shipments 
					if (s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None)) and 
					datetime.strptime((s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None))[:10], "%Y-%m-%d").date() == current_date])
				
				chart_data["created"].append(created)
				chart_data["collected"].append(collected)
				chart_data["delivered"].append(delivered)
				
				current_date += timedelta(days=1)
		
		# Service level breakdown
		service_levels = {}
		for shipment in shipments:
			service = shipment.get("service_type") or "Unknown"
			service_levels[service] = service_levels.get(service, 0) + 1
		
		service_level_list = [{"name": k, "count": v, "label": k, "value": v} for k, v in service_levels.items()]
		
		# Calculate KPIs
		total_value = sum([float(s.get("rate") or s.get("total_value") or s.get("value") or 0) for s in shipments])
		total_weight = sum([float(s.get("charged_weight") or s.get("total_weight") or s.get("weight") or 0) for s in shipments])
		
		avg_rate = total_value / created_count if created_count > 0 else 0
		avg_weight = total_weight / created_count if created_count > 0 else 0
		
		# Calculate average times (if timestamps are available)
		collection_times = []
		delivery_times = []
		for s in shipments:
			s_created = s.get("time_created") or s.get("created_at")
			s_collected = s.get("collected_at") or s.get("collected_date")
			s_delivered = s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None)
			
			if s_created and s_collected:
				try:
					created = datetime.strptime(s_created[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
					collected = datetime.strptime(s_collected[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
					collection_times.append((collected - created).days)
				except:
					pass
			if s_collected and s_delivered:
				try:
					collected = datetime.strptime(s_collected[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
					delivered = datetime.strptime(s_delivered[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
					delivery_times.append((delivered - collected).days)
				except:
					pass
		
		avg_collection_time = sum(collection_times) / len(collection_times) if collection_times else 0
		avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
		
		# Format shipments for display
		formatted_shipments = []
		for s in shipments[:100]:  # Limit to 100 for display
			collection_addr = s.get("collection_address", {})
			delivery_addr = s.get("delivery_address", {})
			
			collection_str = ""
			if isinstance(collection_addr, dict):
				collection_str = ", ".join([
					collection_addr.get("address_line1", ""),
					collection_addr.get("suburb", ""),
					collection_addr.get("city", "")
				]).strip(", ")
			else:
				collection_str = str(collection_addr) if collection_addr else "N/A"
			
			delivery_str = ""
			if isinstance(delivery_addr, dict):
				delivery_str = ", ".join([
					delivery_addr.get("address_line1", ""),
					delivery_addr.get("suburb", ""),
					delivery_addr.get("city", "")
				]).strip(", ")
			else:
				delivery_str = str(delivery_addr) if delivery_addr else "N/A"
			
			formatted_shipments.append({
				"waybill_number": s.get("short_tracking_reference") or s.get("waybill_number") or s.get("tracking_number") or "N/A",
				"status": s.get("status") or "Unknown",
				"service": s.get("service_level_name") or s.get("service_type") or "N/A",
				"collection_address": collection_str or "N/A",
				"delivery_address": delivery_str or "N/A",
				"created": s.get("time_created") or s.get("created_at") or s.get("date") or "N/A"
			})
		
		return {
			"summary": {
				"created": created_count,
				"collected": collected_count,
				"delivered": delivered_count
			},
			"chart_data": chart_data,
			"service_levels": service_level_list,
			"kpis": {
				"avg_rate": round(avg_rate, 2),
				"avg_weight": round(avg_weight, 2),
				"avg_collection_time": round(avg_collection_time, 2),
				"avg_delivery_time": round(avg_delivery_time, 2)
			},
			"shipments": formatted_shipments
		}

