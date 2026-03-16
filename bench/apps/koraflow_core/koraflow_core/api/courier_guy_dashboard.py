"""
Courier Guy Dashboard API
Fetches real-time dashboard data from Courier Guy API
"""
import frappe
from frappe import _
from datetime import datetime as dt, date, timedelta
from koraflow_core.utils.courier_guy_api import CourierGuyAPI


@frappe.whitelist()
def get_historical_shipments(from_date=None, to_date=None, limit=1000):
	"""
	Fetch historical shipments from Courier Guy API
	Used as a fallback when direct API metrics fail
	"""
	try:
		api = CourierGuyAPI()
		# Format dates for API if they are strings
		from_date_str = from_date if isinstance(from_date, str) else (from_date.strftime("%Y-%m-%d") if from_date else None)
		to_date_str = to_date if isinstance(to_date, str) else (to_date.strftime("%Y-%m-%d") if to_date else None)
		
		
		res = api.get_shipments(from_date=from_date_str, to_date=to_date_str, limit=limit)
		if res.get("success"):
			raw_shipments = res.get("shipments", [])
			formatted_shipments = []
			for shipment in raw_shipments:
				collection_addr = shipment.get("collection_address") or {}
				delivery_addr = shipment.get("delivery_address") or {}
				
				if isinstance(collection_addr, dict):
					collection_str = ", ".join(filter(None, [
						collection_addr.get("street_address") or collection_addr.get("entered_address"),
						collection_addr.get("local_area") or collection_addr.get("geo_local_area"),
						collection_addr.get("city") or collection_addr.get("geo_city")
					]))
				else:
					collection_str = str(collection_addr) if collection_addr else "N/A"
				
				if isinstance(delivery_addr, dict):
					delivery_str = ", ".join(filter(None, [
						delivery_addr.get("street_address") or delivery_addr.get("entered_address"),
						delivery_addr.get("local_area") or delivery_addr.get("geo_local_area"),
						delivery_addr.get("city") or delivery_addr.get("geo_city")
					]))
				else:
					delivery_str = str(delivery_addr) if delivery_addr else "N/A"
			
				formatted_shipments.append({
					"waybill_number": shipment.get("short_tracking_reference") or shipment.get("id") or "N/A",
					"tracking_number": shipment.get("short_tracking_reference") or shipment.get("id") or "N/A",
					"status": format_status(shipment.get("status")),
					"service_type": shipment.get("service_level_name") or shipment.get("service_level_code") or "N/A",
					"collection_address": collection_str or "N/A",
					"delivery_address": delivery_str or "N/A",
					"collection_contact_name": collection_addr.get("company") if isinstance(collection_addr, dict) else "N/A",
					"collection_contact_number": collection_addr.get("contact_number") if isinstance(collection_addr, dict) else "N/A",
					"delivery_contact_name": delivery_addr.get("company") if isinstance(delivery_addr, dict) else "N/A",
					"delivery_contact_number": delivery_addr.get("contact_number") if isinstance(delivery_addr, dict) else "N/A",
					"created_at": shipment.get("time_created") or shipment.get("time_modified") or None,
					"collected_at": shipment.get("collected_date") or None,
					"delivered_at": shipment.get("delivered_date") or None,
					"total_value": float(shipment.get("rate") or shipment.get("original_rate") or shipment.get("total_value") or 0),
					"total_weight": float(shipment.get("charged_weight") or shipment.get("actual_weight") or shipment.get("total_weight") or 0),
					"parcel_count": shipment.get("total_pieces") or 1,
					"reference": shipment.get("client_reference") or "",
					"raw_data": shipment
				})
			return {
				"success": True,
				"shipments": formatted_shipments,
				"source": "api_historical"
			}
		return res
	except Exception as e:
		frappe.logger().error(f"Error in get_historical_shipments: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_courier_guy_dashboard_data(from_date=None, to_date=None):
	"""
	Get comprehensive dashboard data from Courier Guy API
	Returns statistics, charts data, KPIs, and shipments list
	
	Args:
		from_date: Start date (YYYY-MM-DD)
		to_date: End date (YYYY-MM-DD)
	"""
	try:
		# Check if integration is enabled
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			# Even if not enabled, return local data
			return get_local_dashboard_data(from_date, to_date)

		try:
			api = CourierGuyAPI()
			frappe.logger().info("Courier Guy Dashboard: API initialized successfully")
			
			# Fetch historical shipments using the dedicated endpoint
			# This ensures we get comprehensive historical data with proper field mapping
			historical_shipments = []
			historical_response = {"success": False, "source": "error"}
			
			# Try direct API call first (more reliable)
			# Note: Ship Logic API doesn't support date params, so we fetch all and filter client-side
			try:
				frappe.logger().info(f"Courier Guy Dashboard: [STEP 1] Starting API call with from_date={from_date}, to_date={to_date}")
				# Format dates for client-side filtering
				try:
					if isinstance(from_date, (dt, date)):
						from_date_str = from_date.strftime("%Y-%m-%d")
						from_date_obj = from_date
					else:
						from_date_str = str(from_date) if from_date else None
						from_date_obj = frappe.utils.getdate(from_date) if from_date else None
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 2] Formatted from_date: {from_date_str}")
				except Exception as date_format_error:
					frappe.logger().error(f"Courier Guy Dashboard: Error formatting from_date: {str(date_format_error)}")
					raise
				
				try:
					if isinstance(to_date, (dt, date)):
						to_date_str = to_date.strftime("%Y-%m-%d")
						to_date_obj = to_date
					else:
						to_date_str = str(to_date) if to_date else None
						to_date_obj = frappe.utils.getdate(to_date) if to_date else None
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 3] Formatted to_date: {to_date_str}")
				except Exception as date_format_error:
					frappe.logger().error(f"Courier Guy Dashboard: Error formatting to_date: {str(date_format_error)}")
					raise
				
				# Call API without date params (fetch all, filter client-side)
				# Note: get_shipments works better without date params, then we filter client-side
				try:
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 4] About to call api.get_shipments (without date params for better reliability)")
					# Try with limit=500 first (more reliable than 1000)
					api_response = api.get_shipments(from_date=from_date_str, to_date=to_date_str, limit=500)
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 5] api.get_shipments returned success={api_response.get('success')}, shipments={len(api_response.get('shipments', []))}")
					if not api_response.get("success"):
						frappe.logger().warning(f"Courier Guy Dashboard: [STEP 5 WARNING] api.get_shipments with limit=500 failed, trying limit=100")
						# Try with smaller limit as fallback
						api_response = api.get_shipments(limit=100)
						frappe.logger().info(f"Courier Guy Dashboard: [STEP 5.1] api.get_shipments(limit=100) returned success={api_response.get('success')}, shipments={len(api_response.get('shipments', []))}")
					if not api_response.get("success"):
						frappe.logger().error(f"Courier Guy Dashboard: [STEP 5 ERROR] api.get_shipments failed even with limit=100: {api_response.get('error', 'Unknown error')}")
						# Don't raise - let it fall through to the else block below
				except Exception as api_call_error:
					import traceback
					error_trace = traceback.format_exc()
					frappe.logger().error(f"Courier Guy Dashboard: [STEP 4 ERROR] api.get_shipments failed: {str(api_call_error)}\n{error_trace}")
					raise
				
				if api_response.get("success") and api_response.get("shipments"):
					raw_shipments = api_response.get("shipments", [])
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 6] Direct API call got {len(raw_shipments)} raw shipments")
					
					# Filter by date client-side if dates provided
					if from_date_obj and to_date_obj and raw_shipments:
						filtered_shipments = []
						for shipment in raw_shipments:
							created_str = shipment.get("time_created") or shipment.get("time_modified")
							if created_str:
								try:
									# Parse ISO format: Handle various formats
									# Examples: "2024-09-10T08:10:33.224915Z", "2024-09-18T06:58:30.40625+00:00"
									date_str = str(created_str).strip()
									# Replace Z with +00:00 if present
									if date_str.endswith('Z'):
										date_str = date_str[:-1] + '+00:00'
									# If no timezone, assume UTC
									elif '+' not in date_str and date_str.count(':') >= 2:
										# Has time but no timezone - try parsing as-is first
										pass
									
									# Try parsing with fromisoformat
									try:
										created_date = dt.fromisoformat(date_str).date()
									except ValueError:
										# Fallback: try parsing without microseconds if that fails
										try:
											# Remove microseconds if present
											if '.' in date_str:
												date_str_no_micro = date_str.split('.')[0] + date_str.split('.')[1].split('+')[0].split('-')[0]
												if '+' in date_str or date_str.endswith('Z'):
													date_str_no_micro += '+00:00'
												created_date = dt.fromisoformat(date_str_no_micro).date()
											else:
												# No microseconds, try adding timezone if missing
												if '+' not in date_str and '-' not in date_str[-6:]:
													date_str += '+00:00'
												created_date = dt.fromisoformat(date_str).date()
										except ValueError:
											# Last resort: try strptime
											for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
												try:
													created_date = dt.strptime(date_str.split('.')[0], fmt).date()
													break
												except ValueError:
													continue
											else:
												# If all parsing fails, include the shipment
												filtered_shipments.append(shipment)
												continue
									
									if from_date_obj <= created_date <= to_date_obj:
										filtered_shipments.append(shipment)
								except Exception as parse_error:
									# If date parsing fails, include the shipment (better to show than hide)
									frappe.logger().debug(f"Courier Guy Dashboard: Date parse error for shipment {shipment.get('short_tracking_reference', 'unknown')}: {str(parse_error)[:100]}")
									filtered_shipments.append(shipment)
							else:
								# If no date, include it
								filtered_shipments.append(shipment)
						raw_shipments = filtered_shipments
						frappe.logger().info(f"Courier Guy Dashboard: [STEP 6.5] After date filtering: {len(raw_shipments)} shipments (from {len(api_response.get('shipments', []))} total)")
					
					# Format shipments using the same logic as get_historical_shipments
					formatted_shipments = []
					shipment_count = 0
					for shipment in raw_shipments:
						shipment_count += 1
						try:
							collection_addr = shipment.get("collection_address") or {}
							delivery_addr = shipment.get("delivery_address") or {}
							
							if isinstance(collection_addr, dict):
								collection_str = ", ".join(filter(None, [
									collection_addr.get("street_address") or collection_addr.get("entered_address"),
									collection_addr.get("local_area") or collection_addr.get("geo_local_area"),
									collection_addr.get("city") or collection_addr.get("geo_city")
								]))
							else:
								collection_str = str(collection_addr) if collection_addr else "N/A"
							
							if isinstance(delivery_addr, dict):
								delivery_str = ", ".join(filter(None, [
									delivery_addr.get("street_address") or delivery_addr.get("entered_address"),
									delivery_addr.get("local_area") or delivery_addr.get("geo_local_area"),
									delivery_addr.get("city") or delivery_addr.get("geo_city")
								]))
							else:
								delivery_str = str(delivery_addr) if delivery_addr else "N/A"
						
							formatted_shipments.append({
								"waybill_number": shipment.get("short_tracking_reference") or shipment.get("id") or "N/A",
								"tracking_number": shipment.get("short_tracking_reference") or shipment.get("id") or "N/A",
								"status": format_status(shipment.get("status")),
								"service_type": shipment.get("service_level_name") or shipment.get("service_level_code") or "N/A",
								"collection_address": collection_str or "N/A",
								"delivery_address": delivery_str or "N/A",
								"collection_contact_name": collection_addr.get("company") if isinstance(collection_addr, dict) else "N/A",
								"collection_contact_number": collection_addr.get("contact_number") if isinstance(collection_addr, dict) else "N/A",
								"delivery_contact_name": delivery_addr.get("company") if isinstance(delivery_addr, dict) else "N/A",
								"delivery_contact_number": delivery_addr.get("contact_number") if isinstance(delivery_addr, dict) else "N/A",
								"created_at": shipment.get("time_created") or shipment.get("time_modified") or None,
								"collected_at": shipment.get("collected_date") or None,
								"delivered_at": shipment.get("delivered_date") or None,
								"total_value": float(shipment.get("rate") or shipment.get("original_rate") or shipment.get("total_value") or 0),
								"total_weight": float(shipment.get("charged_weight") or shipment.get("actual_weight") or shipment.get("total_weight") or 0),
								"parcel_count": shipment.get("total_pieces") or 1,
								"reference": shipment.get("client_reference") or "",
								"raw_data": shipment
							})
						except Exception as format_shipment_error:
							frappe.logger().error(f"Courier Guy Dashboard: [STEP 7 ERROR] Error formatting shipment {shipment_count}: {str(format_shipment_error)}")
							# Continue with next shipment instead of failing completely
							continue
					
					frappe.logger().info(f"Courier Guy Dashboard: [STEP 8] Successfully formatted {len(formatted_shipments)} out of {len(raw_shipments)} shipments")
					
					historical_shipments = formatted_shipments
					historical_response = {"success": True, "source": "api", "shipments": formatted_shipments}
					frappe.logger().info(f"Courier Guy Dashboard: ✅ Successfully formatted {len(historical_shipments)} shipments from direct API call")
				else:
					error_msg = api_response.get('error', 'Unknown error') if not api_response.get("success") else "No shipments returned"
					frappe.logger().warning(f"Courier Guy Dashboard: Direct API call returned success=False or no shipments. Error: {error_msg}, Response keys: {list(api_response.keys())}")
					# Try fallback immediately instead of raising exception
					try:
						frappe.logger().info(f"Courier Guy Dashboard: Falling back to get_historical_shipments (direct API returned no shipments)")
						historical_response = get_historical_shipments(from_date=from_date, to_date=to_date, limit=1000)
						historical_shipments = historical_response.get("shipments", []) if historical_response.get("success") else []
						frappe.logger().info(f"Courier Guy Dashboard: get_historical_shipments returned {len(historical_shipments)} shipments, source: {historical_response.get('source')}")
					except Exception as fallback_error:
						frappe.logger().error(f"Courier Guy Dashboard: Fallback to get_historical_shipments also failed: {str(fallback_error)[:200]}")
						historical_shipments = []
						historical_response = {"success": False, "source": "error"}
			except Exception as direct_api_error:
				import traceback
				error_trace = traceback.format_exc()[:1000]
				frappe.logger().error(f"Courier Guy Dashboard: Direct API call failed: {str(direct_api_error)}\n{error_trace}")
				# Fall back to get_historical_shipments
				try:
					frappe.logger().info(f"Courier Guy Dashboard: Falling back to get_historical_shipments")
					# Use the imported function from top of file
					historical_response = get_historical_shipments(from_date=from_date, to_date=to_date, limit=1000)
					historical_shipments = historical_response.get("shipments", []) if historical_response.get("success") else []
					frappe.logger().info(f"Courier Guy Dashboard: get_historical_shipments returned {len(historical_shipments)} shipments, source: {historical_response.get('source')}")
				except Exception as hist_error:
					frappe.logger().error(f"Courier Guy Dashboard: get_historical_shipments also failed: {str(hist_error)[:200]}")
					historical_shipments = []
					historical_response = {"success": False, "source": "error"}
			
			merged_shipments = historical_shipments.copy() if historical_shipments else []
			
			# Sort by created date (newest first)
			merged_shipments.sort(
				key=lambda x: x.get("created_at") or x.get("created") or x.get("date") or "",
				reverse=True
			)
			
			# Calculate summary statistics from merged shipments
			created_count = len(merged_shipments)
			collected_count = len([s for s in merged_shipments if s.get("status") and s.get("status").lower() in [
				"collected", "in-transit", "in transit", "out-for-delivery", "out for delivery", "delivered", "collection request", "collection assigned"
			]])
			delivered_count = len([s for s in merged_shipments if s.get("status") and s.get("status").lower() == "delivered"])
			
			# Calculate stats from merged shipments
			stats = {
				"total_shipments": created_count,
				"in_transit": len([s for s in merged_shipments if s.get("status") and s.get("status").lower() in ["in-transit", "in transit", "collection request", "collection assigned", "out-for-delivery", "out for delivery"]]),
				"delivered": delivered_count,
				"pending": len([s for s in merged_shipments if s.get("status") and s.get("status").lower() in ["draft", "created", "pending", "pending pickup"]]),
				"failed": len([s for s in merged_shipments if s.get("status") and s.get("status").lower() in ["failed", "cancelled", "collection failed attempt"]])
			}
			
			try:
				# Calculate from merged shipments
				chart_data = calculate_chart_data(merged_shipments, from_date, to_date)
				service_levels = calculate_service_levels(merged_shipments)
				kpis = calculate_kpis(merged_shipments)
			except Exception as calc_error:
				import traceback
				frappe.logger().error(f"Courier Guy Dashboard: Error calculating charts/KPIs: {str(calc_error)}\n{traceback.format_exc()[:500]}")
				# Use empty defaults
				chart_data = {"labels": [], "created": [], "collected": [], "delivered": []}
				service_levels = []
				kpis = {}
			
			# Format shipments for display (limit to 100 for table)
			try:
				formatted_shipments = format_shipments_for_display(merged_shipments[:100])
			except Exception as format_error:
				import traceback
				frappe.logger().error(f"Courier Guy Dashboard: Error formatting shipments: {str(format_error)}\n{traceback.format_exc()[:500]}")
				# Return raw shipments if formatting fails
				formatted_shipments = merged_shipments[:100]
			
			return {
				"success": True,
				"data": {
					"summary": {
						"created": created_count,
						"collected": collected_count,
						"delivered": delivered_count
					},
					"stats": stats,
					"chart_data": chart_data,
					"service_levels": service_levels,
					"kpis": kpis,
					"shipments": formatted_shipments,
					"source": historical_response.get("source", "api"),
					"total_shipments_count": len(merged_shipments),
					"from_date": from_date,
					"to_date": to_date
				}
			}
		except Exception as api_error:
			# If API call fails, log the error and fall back to local data
			import traceback
			error_summary = str(api_error)[:500] if len(str(api_error)) > 500 else str(api_error)
			error_trace = traceback.format_exc()[:2000]  # Increased trace length
			# Log to both logger and error log with full details
			error_msg = f"Courier Guy API dashboard call failed: {error_summary}\n{error_trace}"
			frappe.logger().error(error_msg)
			frappe.log_error(title="Courier Guy Dashboard", message=error_msg)
			# Print to console for immediate debugging
			print(f"\n{'='*60}")
			print(f"DEBUG: Courier Guy Dashboard Exception Caught!")
			print(f"Error: {error_summary}")
			print(f"Trace: {error_trace[:500]}")
			print(f"{'='*60}\n")
			
			# Check if it's a network/DNS error
			error_str = str(api_error).lower()
			is_network_error = any(keyword in error_str for keyword in ['name resolution', 'dns', 'connection', 'network', 'resolve host'])
			
			# Get local data
			local_data = get_local_dashboard_data(from_date, to_date)
			
			# Add warning if it's a network error
			if is_network_error and local_data.get("success"):
				local_data["data"]["api_warning"] = "Unable to connect to Courier Guy API. Showing local waybills only. Please check network connectivity and API URL settings."
			
			return local_data
			
	except Exception as e:
		# Log error summary (truncated to avoid CharacterLengthExceededError)
		error_summary = str(e)[:100] if len(str(e)) > 100 else str(e)
		frappe.logger().debug(f"Error fetching Courier Guy dashboard (trying local data): {error_summary}")
		# Fallback to local data
		try:
			return get_local_dashboard_data(from_date, to_date)
		except Exception as local_error:
			# If local data also fails, return error response
			local_error_summary = str(local_error)[:100] if len(str(local_error)) > 100 else str(local_error)
			frappe.log_error(title="Courier Guy Dashboard", message=f"Error getting local dashboard data: {local_error_summary}")
			return {
				"success": False,
				"error": "Unable to load dashboard data. Please check error logs."
			}


def get_local_dashboard_data(from_date=None, to_date=None):
	"""
	Get comprehensive dashboard data from local ERPNext waybills
	Fallback when API dashboard is not available
	"""
	try:
		# Set default date range (last 30 days if not provided to capture more data)
		if not to_date:
			to_date = dt.now().date()
		else:
			if isinstance(to_date, str):
				to_date = frappe.utils.getdate(to_date)
			else:
				to_date = to_date
		
		if not from_date:
			# Default to 30 days ago to capture more historical data
			from_date = to_date - timedelta(days=30)
		else:
			if isinstance(from_date, str):
				from_date = frappe.utils.getdate(from_date)
			else:
				from_date = from_date
		
		# Log date range for debugging
		frappe.logger().debug(f"Courier Guy Dashboard: Fetching data from {from_date} to {to_date}")
		
		# Build filters
		# Use direct SQL query to avoid Frappe's automatic order_by generation
		# which causes SQL syntax errors with DocType names containing spaces
		from_date_str = frappe.utils.formatdate(from_date, "yyyy-MM-dd")
		to_date_str = frappe.utils.formatdate(to_date, "yyyy-MM-dd")
		
		# Use frappe.db.sql to avoid automatic order_by issues
		# Note: Using correct field names from DocType (pickup_address, not collection_address)
		waybills_data = frappe.db.sql("""
			SELECT 
				name, waybill_number, status, service_type, delivery_city,
				delivery_address, pickup_address, creation, total_value,
				total_weight
			FROM `tabCourier Guy Waybill`
			WHERE DATE(creation) BETWEEN %s AND %s
		""", (from_date_str, to_date_str), as_dict=True)
		
		# Convert to list of dicts and sort by creation date (newest first)
		all_waybills = list(waybills_data)
		all_waybills.sort(
			key=lambda x: frappe.utils.get_datetime(x.get("creation")) if x.get("creation") else frappe.utils.now_datetime(),
			reverse=True
		)
		
		# Rename 'creation' to 'created' for consistency with rest of code
		for wb in all_waybills:
			if 'creation' in wb:
				wb['created'] = wb.pop('creation')
		
		# Calculate summary counts
		created_count = len(all_waybills)
		# Note: collected_date and delivered_date may not exist in DocType
		# Use status to determine collected/delivered counts
		collected_count = len([w for w in all_waybills if w.get("status") in ["In Transit", "Delivered", "Out for Delivery"]])
		delivered_count = len([w for w in all_waybills if w.get("status") == "Delivered"])
		
		# Get statistics by status
		stats = {
			"total_shipments": created_count,
			"in_transit": len([w for w in all_waybills if w.get("status") == "In Transit"]),
			"delivered": delivered_count,
			"pending": len([w for w in all_waybills if w.get("status") in ["Draft", "Created", "Pending Pickup"]]),
			"failed": len([w for w in all_waybills if w.get("status") == "Failed"])
		}
		
		# Log stats for debugging
		frappe.logger().debug(f"Courier Guy Dashboard: Calculated stats - {stats}")
		
		# Prepare chart data - group by date
		chart_data = {
			"labels": [],
			"created": [],
			"collected": [],
			"delivered": []
		}
		
		current_date = from_date
		while current_date <= to_date:
			date_str = current_date.strftime("%d/%m/%y")
			chart_data["labels"].append(date_str)
			
			# Count for this date
			created = len([w for w in all_waybills if w.get("created") and frappe.utils.getdate(w.get("created")) == current_date])
			# Use status to determine collected (any status beyond "Created" or "Draft")
			collected = len([w for w in all_waybills 
				if w.get("created") and frappe.utils.getdate(w.get("created")) == current_date
				and w.get("status") in ["In Transit", "Delivered", "Out for Delivery"]])
			# Count delivered by status
			delivered = len([w for w in all_waybills 
				if w.get("created") and frappe.utils.getdate(w.get("created")) == current_date
				and w.get("status") == "Delivered"])
			
			chart_data["created"].append(created)
			chart_data["collected"].append(collected)
			chart_data["delivered"].append(delivered)
			
			current_date += timedelta(days=1)
		
		# Service level breakdown
		service_levels = {}
		for waybill in all_waybills:
			service = waybill.get("service_type") or "Unknown"
			service_levels[service] = service_levels.get(service, 0) + 1
		
		# Format for chart (support both formats for compatibility)
		service_level_list = [
			{"name": k, "count": v, "label": k, "value": v} 
			for k, v in service_levels.items()
		]
		
		# Calculate KPIs
		total_value = sum([float(w.get("total_value") or 0) for w in all_waybills])
		total_weight = sum([float(w.get("total_weight") or 0) for w in all_waybills])
		delivered_waybills = [w for w in all_waybills if w.get("status") == "Delivered"]
		collected_waybills = [w for w in all_waybills if w.get("status") in ["In Transit", "Delivered", "Out for Delivery"]]
		
		avg_rate = total_value / created_count if created_count > 0 else 0
		avg_weight = total_weight / created_count if created_count > 0 else 0
		
		# Calculate average collection time
		# Since we don't have collected_date, we'll use a simplified calculation
		# For now, set to 0 or use a default estimate
		avg_collection_time = 0  # Can be enhanced if tracking history provides collection timestamps
		
		# Calculate average delivery time
		# Since we don't have delivered_date, we'll use a simplified calculation
		avg_delivery_time = 0  # Can be enhanced if tracking history provides delivery timestamps
		
		# Format shipments list
		formatted_shipments = []
		for shipment in all_waybills[:100]:  # Limit to 100 for display
			# Format addresses - use pickup_address (not collection_address)
			collection_addr = shipment.get("pickup_address") or "N/A"
			delivery_addr = shipment.get("delivery_address") or shipment.get("delivery_city") or "N/A"
			
			formatted_shipments.append({
				"waybill_number": shipment.get("waybill_number") or shipment.get("name"),
				"status": format_status(shipment.get("status")),
				"service": shipment.get("service_type") or "N/A",
				"collection_address": collection_addr,
				"delivery_address": delivery_addr,
				"created": frappe.format(shipment.get("created"), {"fieldtype": "Datetime"}) if shipment.get("created") else "N/A"
			})

		return {
			"success": True,
			"data": {
				"summary": {
					"created": created_count,
					"collected": collected_count,
					"delivered": delivered_count
				},
				"stats": stats,
				"chart_data": chart_data,
				"service_levels": service_level_list,
				"kpis": {
					"avg_rate": round(avg_rate, 2),
					"avg_weight": round(avg_weight, 2),
					"avg_collection_time": round(avg_collection_time, 2),
					"avg_delivery_time": round(avg_delivery_time, 2)
				},
				"shipments": formatted_shipments,
				"source": "local",
				"from_date": from_date.strftime("%Y-%m-%d"),
				"to_date": to_date.strftime("%Y-%m-%d")
			}
		}

	except Exception as e:
		frappe.log_error(title="Courier Guy Dashboard", message=f"Error getting local dashboard data: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


def calculate_chart_data(shipments, from_date=None, to_date=None):
	"""
	Calculate chart data from shipments list
	"""
	
	chart_data = {"labels": [], "created": [], "collected": [], "delivered": []}
	
	if not from_date or not to_date:
		return chart_data
	
	# Ensure dates are date objects
	if isinstance(from_date, str):
		from_date = frappe.utils.getdate(from_date)
	if isinstance(to_date, str):
		to_date = frappe.utils.getdate(to_date)
	
	current_date = from_date
	while current_date <= to_date:
		date_str = current_date.strftime("%d/%m/%y")
		chart_data["labels"].append(date_str)
		
		# Count shipments for this date
		# Ship Logic uses 'time_created', fallback to 'created_at'
		created = len([s for s in shipments 
			if (s.get("time_created") or s.get("created_at")) and 
			frappe.utils.getdate((s.get("time_created") or s.get("created_at"))[:10]) == current_date])
		collected = len([s for s in shipments 
			if (s.get("collected_at") or s.get("collected_date")) and 
			frappe.utils.getdate((s.get("collected_at") or s.get("collected_date"))[:10]) == current_date])
		delivered = len([s for s in shipments 
			if (s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None)) and 
			frappe.utils.getdate((s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None))[:10]) == current_date])
		
		chart_data["created"].append(created)
		chart_data["collected"].append(collected)
		chart_data["delivered"].append(delivered)
		
		current_date += timedelta(days=1)
	
	return chart_data


def calculate_service_levels(shipments):
	"""
	Calculate service level breakdown from shipments
	"""
	service_levels = {}
	for shipment in shipments:
		service = shipment.get("service_type") or shipment.get("service") or "Unknown"
		service_levels[service] = service_levels.get(service, 0) + 1
	
	return [{"name": k, "count": v, "label": k, "value": v} for k, v in service_levels.items()]


def calculate_kpis(shipments):
	"""
	Calculate KPIs from shipments
	"""
	if not shipments:
		return {
			"avg_rate": 0,
			"avg_weight": 0,
			"avg_collection_time": 0,
			"avg_delivery_time": 0
		}
	
	# Ship Logic uses 'rate' and 'charged_weight'
	total_value = sum([float(s.get("rate") or s.get("total_value") or s.get("value") or 0) for s in shipments])
	total_weight = sum([float(s.get("charged_weight") or s.get("total_weight") or s.get("weight") or 0) for s in shipments])
	
	avg_rate = total_value / len(shipments) if shipments else 0
	avg_weight = total_weight / len(shipments) if shipments else 0
	
	# Calculate average times if timestamps are available
	collection_times = []
	delivery_times = []
	
	for s in shipments:
		s_created = s.get("time_created") or s.get("created_at")
		s_collected = s.get("collected_at") or s.get("collected_date")
		# For delivered_at, Ship Logic sometimes only has time_modified if status is Delivered
		s_delivered = s.get("delivered_at") or s.get("delivered_date") or (s.get("time_modified") if s.get("status") == "Delivered" else None)
		
		if s_created and s_collected:
			try:
				created = dt.strptime(s_created[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
				collected = dt.strptime(s_collected[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
				collection_times.append((collected - created).days)
			except:
				pass
		if s_collected and s_delivered:
			try:
				collected = dt.strptime(s_collected[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
				delivered = dt.strptime(s_delivered[:19].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
				delivery_times.append((delivered - collected).days)
			except:
				pass
	
	avg_collection_time = sum(collection_times) / len(collection_times) if collection_times else 0
	avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
	
	return {
		"avg_rate": round(avg_rate, 2),
		"avg_weight": round(avg_weight, 2),
		"avg_collection_time": round(avg_collection_time, 2),
		"avg_delivery_time": round(avg_delivery_time, 2)
	}


def format_status(raw_status):
	"""
	Normalize status strings (e.g. "collection-assigned" -> "Collection Request")
	"""
	if not raw_status:
		return "Unknown"
		
	status = str(raw_status).replace("-", " ").title()
	if status == "Collection Assigned":
		return "Collection Request"
	return status


def extract_waybill_fields(wb_data):
	"""Robustly extract fields from waybill data (API or Local)"""
	if not wb_data:
		return {}
	

	# Handle both dict and Frappe document
	def get(k, default=None):
		if isinstance(wb_data, dict):
			return wb_data.get(k, default)
		return getattr(wb_data, k, default) if hasattr(wb_data, k) or (isinstance(wb_data, object) and k in wb_data.__dict__) else default

	
	# Ship Logic API uses 'delivery_to' object for delivery contact
	delivery_to = wb_data.get("delivery_to", {}) or {}
	if isinstance(delivery_to, dict):
		delivery_contact_name = delivery_to.get("name") or delivery_to.get("contact_name") or delivery_to.get("contact")
		delivery_contact_number = delivery_to.get("mobile_number") or delivery_to.get("phone") or delivery_to.get("mobile")
		delivery_email = delivery_to.get("email")
	else:
		delivery_contact_name = None
		delivery_contact_number = None
		delivery_email = None
	
	# Also check nested delivery_contact structure and alternative names
	del_contact = wb_data.get("delivery_contact", {}) or wb_data.get("to_contact", {}) or wb_data.get("recipient", {}) or wb_data.get("receiver", {}) or wb_data.get("consignee", {}) or {}
	if isinstance(del_contact, dict):
		delivery_contact_name = delivery_contact_name or del_contact.get("name") or del_contact.get("contact_name") or del_contact.get("contact")
		delivery_contact_number = delivery_contact_number or del_contact.get("mobile_number") or del_contact.get("phone") or del_contact.get("mobile")
		delivery_email = delivery_email or del_contact.get("email")
	
	# Flat field fallbacks
	delivery_contact_name = delivery_contact_name or wb_data.get("delivery_contact_name") or wb_data.get("to_name") or wb_data.get("recipient_name") or wb_data.get("receiver_name")
	delivery_contact_number = delivery_contact_number or wb_data.get("delivery_contact_number") or wb_data.get("to_phone") or wb_data.get("recipient_phone") or wb_data.get("receiver_phone")
	delivery_email = delivery_email or wb_data.get("delivery_email") or wb_data.get("to_email")
	
	# Collection contact - Ship Logic uses 'collection_from' as a string for the name
	collection_from = wb_data.get("collection_from") or ""
	coll_contact = wb_data.get("collection_contact", {}) or wb_data.get("from_contact", {}) or wb_data.get("sender", {}) or {}
	if isinstance(coll_contact, dict):
		collection_contact_name = collection_from or coll_contact.get("name") or coll_contact.get("contact_name") or coll_contact.get("contact")
		collection_contact_number = coll_contact.get("mobile_number") or coll_contact.get("phone") or coll_contact.get("mobile")
	else:
		collection_contact_name = str(collection_from)
		collection_contact_number = None
	
	# Address logic - Ship Logic uses 'entered_address' as full string
	# Also check to_address/from_address as alternative field names
	coll_addr = get("collection_address", {}) or get("from_address", {}) or {}
	del_addr = get("delivery_address", {}) or get("to_address", {}) or {}

	
	# If addresses are dicts, enrich them with additional fields we may find
	if isinstance(del_addr, dict):
		# Ship Logic puts full address in 'entered_address'
		entered = del_addr.get("entered_address", "")
		if entered and not del_addr.get("street_address"):
			del_addr["street_address"] = entered
		# local_area often contains suburb
		if del_addr.get("local_area") and not del_addr.get("suburb"):
			del_addr["suburb"] = del_addr.get("local_area")
		if del_addr.get("geo_city") and not del_addr.get("city"):
			del_addr["city"] = del_addr.get("geo_city")
		if del_addr.get("code") and not del_addr.get("postal_code"):
			del_addr["postal_code"] = del_addr.get("code")
		if del_addr.get("zone") and not del_addr.get("province"):
			del_addr["province"] = del_addr.get("zone")
	
	if isinstance(coll_addr, dict):
		entered = coll_addr.get("entered_address", "")
		if entered and not coll_addr.get("street_address"):
			coll_addr["street_address"] = entered
		if coll_addr.get("local_area") and not coll_addr.get("suburb"):
			coll_addr["suburb"] = coll_addr.get("local_area")
		if coll_addr.get("geo_city") and not coll_addr.get("city"):
			coll_addr["city"] = coll_addr.get("geo_city")
	
	# If local Frappe doc, some keys vary
	if not isinstance(wb_data, dict):
		coll_addr = {
			"street_address": get("pickup_address"),
			"city": get("pickup_city"),
			"suburb": get("pickup_suburb"),
			"postal_code": get("pickup_postal_code")
		}
		del_addr = {
			"street_address": get("delivery_address"),
			"city": get("delivery_city"),
			"suburb": get("delivery_suburb"),
			"postal_code": get("delivery_postal_code")
		}
		delivery_contact_name = get("delivery_contact_name")
		delivery_contact_number = get("delivery_contact_phone")
		delivery_email = get("delivery_contact_email")
		collection_contact_name = get("pickup_contact_name")
		collection_contact_number = get("pickup_contact_phone")

	# Calculate parcel count from parcels array if available
	parcels = get("parcels", [])
	parcel_count = len(parcels) if isinstance(parcels, list) and parcels else get("parcel_count") or 1

	return {
		"waybill_number": get("short_tracking_reference") or get("custom_tracking_reference") or get("waybill_number") or get("id") or (str(wb_data.name) if not isinstance(wb_data, dict) else None),
		"status": format_status(get("status")),
		"service_level": get("service_level_name") or get("service_level_code") or get("service_type"),
		"collection_address": coll_addr,
		"delivery_address": del_addr,
		"collection_contact_name": collection_contact_name or get("collection_contact_name") or get("pickup_contact_name") or (coll_addr.get("company") if isinstance(coll_addr, dict) else None),
		"collection_contact_number": collection_contact_number or get("collection_contact_number") or get("pickup_contact_phone") or (coll_addr.get("contact_number") if isinstance(coll_addr, dict) else None),
		"delivery_contact_name": delivery_contact_name or get("delivery_contact_name") or (del_addr.get("company") if isinstance(del_addr, dict) else None),
		"delivery_contact_number": delivery_contact_number or get("delivery_contact_number") or get("delivery_contact_phone") or (del_addr.get("contact_number") if isinstance(del_addr, dict) else None),
		"delivery_email": delivery_email or get("delivery_contact_email") or get("delivery_email"),
		"created_at": get("time_created") or get("shipment_time_created") or get("created_at") or get("creation"),
		"collected_at": get("collected_date") or get("shipment_collected_date") or get("collected_at"),
		"delivered_at": get("delivered_date") or get("shipment_delivered_date") or get("delivered_at"),
		"estimated_delivery_at": get("estimated_delivery_from") or get("estimated_delivery_to") or get("estimated_delivery_date") or get("estimated_delivery_at"),
		"total_value": get("rate") or get("original_rate") or get("total_value"),
		"rate": get("rate") or get("original_rate") or get("total_value"),
		"charged_weight": get("charged_weight") or get("actual_weight") or get("total_weight"),
		"actual_weight": get("actual_weight"),
		"volumetric_weight": get("volumetric_weight"),
		"customer_reference": get("customer_reference") or get("custom_tracking_reference") or get("reference") or get("client_reference"),
		"parcel_count": parcel_count,
		# Ship Logic /shipments uses collection_branch_name/delivery_branch_name for hub codes
		# /tracking endpoint uses collection_hub/delivery_hub
		"from_hub": get("collection_branch_name") or get("collection_hub") or get("from_hub_code") or get("from_hub"),
		"to_hub": get("delivery_branch_name") or get("delivery_hub") or get("to_hub_code") or get("to_hub"),
		"collection_min": get("collection_min_date") or get("collection_min_time"),
		"collection_max": get("collection_before"),
		"delivery_min": get("delivery_min_date") or get("delivery_min_time"),
		"delivery_max": get("delivery_before"),
	}




def format_shipments_for_display(shipments):
	"""
	Format shipments for dashboard display
	"""
	formatted = []
	for shipment in shipments:
		# Extract address information
		collection_addr = shipment.get("collection_address") or {}
		delivery_addr = shipment.get("delivery_address") or {}
		
		collection_str = "N/A"
		delivery_str = "N/A"
		
		# Format addresses if they're strings
		if isinstance(collection_addr, str):
			collection_str = collection_addr if len(collection_addr) <= 50 else collection_addr[:47] + "..."
		elif isinstance(collection_addr, dict):
			# If it's a dict, we might want to flatten it or keep it as object?
			# The frontend expects a string or object.
			# Let's keep it as object but ensure it has keys needed if we want to display it
			# But for table display, the frontend format_address handles object
			collection_str = collection_addr # Pass the object
			
		if isinstance(delivery_addr, str):
			delivery_str = delivery_addr if len(delivery_addr) <= 50 else delivery_addr[:47] + "..."
		elif isinstance(delivery_addr, dict):
			delivery_str = delivery_addr

		# Extract contact info
		coll_name = shipment.get("collection_contact_name")
		coll_phone = shipment.get("collection_contact_number")
		if isinstance(collection_addr, dict):
			if not coll_name: coll_name = collection_addr.get("contact_name")
			if not coll_phone: coll_phone = collection_addr.get("contact_phone")
			
		del_name = shipment.get("delivery_contact_name")
		del_phone = shipment.get("delivery_contact_number")
		if isinstance(delivery_addr, dict):
			if not del_name: del_name = delivery_addr.get("contact_name")
			if not del_phone: del_phone = delivery_addr.get("contact_phone")
		
		formatted.append({
			"waybill_number": shipment.get("short_tracking_reference") or shipment.get("waybill_number") or shipment.get("name") or "N/A",
			"status": format_status(shipment.get("status")),
			"service": shipment.get("service_level_name") or shipment.get("service_type") or shipment.get("service") or "N/A",
			"collection_address": collection_str,
			"delivery_address": delivery_str,
			"created": shipment.get("time_created") or shipment.get("created_at") or shipment.get("created") or shipment.get("date") or "N/A",
			# Extra fields for filtering
			"collection_contact_name": coll_name,
			"collection_contact_number": coll_phone,
			"delivery_contact_name": del_name,
			"delivery_contact_number": del_phone,
			# Pass raw API data for detailed shipment view
			"raw_data": shipment.get("raw_data") or shipment
		})
	
	return formatted


@frappe.whitelist()
def sync_courier_guy_data():
	"""
	Sync data from Courier Guy API to local waybills
	Updates tracking status for all waybills
	"""
	try:
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return {"success": False, "error": "Integration not enabled"}

		# Get all waybills with tracking numbers
		waybills = frappe.get_all(
			"Courier Guy Waybill",
			filters={"tracking_number": ["!=", ""]},
			fields=["name", "tracking_number"]
		)

		updated = 0
		api = CourierGuyAPI()

		for waybill in waybills:
			try:
				waybill_doc = frappe.get_doc("Courier Guy Waybill", waybill.name)
				waybill_doc.update_tracking()
				updated += 1
			except Exception as e:
				frappe.log_error(title="Courier Guy Sync", message=f"Error updating waybill {waybill.name}: {str(e)}")

		return {
			"success": True,
			"message": f"Updated {updated} waybills",
			"updated": updated
		}

	except Exception as e:
		frappe.log_error(title="Courier Guy Sync", message=f"Error syncing Courier Guy data: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_waybill_details(waybill_number):
	"""
	Get full waybill details for modal display
	"""
	try:
		# Check if integration is enabled
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return get_local_waybill_details(waybill_number)

		# Initialize API
		api = CourierGuyAPI()
		waybill_number = str(waybill_number).strip().upper()
		frappe.logger().info(f"Courier Guy Dashboard: Fetching details for {waybill_number}")
		
		# 1. Try to get full shipment record (best for address/contact details)
		full_res = api.get_shipment_by_waybill(waybill_number)
		shipment = full_res.get("data") if full_res.get("success") else None
		
		# 2. Get tracking info for events
		tracking_res = api.get_tracking(waybill_number)
		trk_data = tracking_res.get("raw_response", {}) if tracking_res.get("success") else {}
		
		# If we have nested structure in tracking
		if isinstance(trk_data, dict) and "shipments" in trk_data:
			shipments_list = trk_data.get("shipments", [])
			if shipments_list: trk_data = shipments_list[0]
			
		# 3. Merge and extract
		# If we found a full shipment, it's our base data. Otherwise use tracking data.
		base_data = shipment or trk_data
		if not base_data:
			return {"success": False, "error": f"Waybill {waybill_number} not found"}
			
		# Enriched fields logic
		data = extract_waybill_fields(base_data)
		data["tracking_history"] = tracking_res.get("history", []) or tracking_res.get("tracking_events", []) or []
		data["raw_data"] = base_data
		
		# Merge useful fields from tracking API if not in base data
		if tracking_res.get("success"):
			if tracking_res.get("collection_hub") and not data.get("from_hub"):
				data["from_hub"] = tracking_res["collection_hub"]
			if tracking_res.get("delivery_hub") and not data.get("to_hub"):
				data["to_hub"] = tracking_res["delivery_hub"]
			if tracking_res.get("service_level_name") and not data.get("service_level"):
				data["service_level"] = tracking_res["service_level_name"]
				
		data["note"] = "Fully enriched shipment details" if shipment else "Tracking data only (Full record not found)"
		
		return {"success": True, "data": data}

	except Exception as e:
		frappe.log_error(title="Courier Guy Dashboard", message=f"Error fetching waybill details: {str(e)}")
		# Fallback to local
		return get_local_waybill_details(waybill_number)


def get_local_waybill_details(waybill_number):
	"""Get waybill details from local database"""
	try:
		if not frappe.db.exists("Courier Guy Waybill", {"waybill_number": waybill_number}):
			return {
				"success": False,
				"error": "Waybill not found"
			}
			
		waybill = frappe.get_doc("Courier Guy Waybill", {"waybill_number": waybill_number})
		
		data = extract_waybill_fields(waybill)
		data["source"] = "local"
		data["tracking_history"] = []
		
		return {
			"success": True,
			"data": data
		}
	except Exception as e:
		return {
			"success": False,
			"error": f"Waybill not found: {str(e)}"
		}
