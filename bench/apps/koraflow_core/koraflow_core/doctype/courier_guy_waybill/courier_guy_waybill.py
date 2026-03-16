"""
Courier Guy Waybill Controller
"""
import frappe
import json
from frappe.model.document import Document
from koraflow_core.utils.courier_guy_api import CourierGuyAPI


class CourierGuyWaybill(Document):
	def validate(self):
		"""Validate waybill data"""
		if not self.delivery_note:
			frappe.throw("Delivery Note is required")
		
		# Load delivery note details if not set
		if self.delivery_note and not self.customer:
			dn = frappe.get_doc("Delivery Note", self.delivery_note)
			self.customer = dn.customer
			
			# Try to find patient from customer
			if dn.customer:
				patient = frappe.db.get_value("Patient", {"customer": dn.customer}, "name")
				if patient:
					self.patient = patient
	
	def before_save(self):
		"""Populate address details from delivery note"""
		if self.delivery_note:
			dn = frappe.get_doc("Delivery Note", self.delivery_note)
			
			# Populate delivery address from delivery note
			if dn.shipping_address_name:
				address = frappe.get_doc("Address", dn.shipping_address_name)
				self.delivery_name = address.address_title or dn.customer_name
				self.delivery_address = address.address_line1
				if address.address_line2:
					self.delivery_address += "\n" + address.address_line2
				self.delivery_suburb = address.city
				self.delivery_city = address.city
				self.delivery_postal_code = address.pincode
				self.delivery_country = address.country or "South Africa"
				
				# Get contact details
				if dn.contact_person:
					contact = frappe.get_doc("Contact", dn.contact_person)
					self.delivery_contact_name = contact.first_name
					if contact.last_name:
						self.delivery_contact_name += " " + contact.last_name
					self.delivery_contact_phone = contact.mobile_no or contact.phone
					self.delivery_contact_email = contact.email_id
			
			# Populate pickup address from settings
			settings = frappe.get_single("Courier Guy Settings")
			if settings.enabled:
				self.pickup_name = settings.pickup_contact_name or "Company"
				self.pickup_address = settings.default_pickup_address
				self.pickup_suburb = settings.pickup_suburb
				self.pickup_city = settings.pickup_city
				self.pickup_postal_code = settings.pickup_postal_code
				self.pickup_country = settings.pickup_country or "South Africa"
				self.pickup_contact_name = settings.pickup_contact_name
				self.pickup_contact_phone = settings.pickup_contact_phone
				self.pickup_contact_email = settings.pickup_contact_email
			
			# Calculate weight and value from items
			if not self.total_weight:
				total_weight = 0
				for item in dn.items:
					if item.weight_per_unit:
						total_weight += item.weight_per_unit * item.qty
				self.total_weight = total_weight or 1.0  # Default 1kg if not specified
			
			if not self.total_value:
				self.total_value = dn.grand_total
	
	def on_submit(self):
		"""Create waybill in Courier Guy system"""
		if self.status == "Draft" or not self.waybill_number:
			self.create_waybill()
	
	def create_waybill(self):
		"""Create waybill via Courier Guy API"""
		try:
			api = CourierGuyAPI()
			response = api.create_waybill(self)
			
			if response.get("success"):
				self.waybill_number = response.get("waybill_number")
				self.tracking_number = response.get("tracking_number")
				self.status = "Created"
				self.api_response = json.dumps(response, indent=2)
				self.error_message = None
				
				# Save without triggering hooks
				self.flags.ignore_validate = True
				self.save()
				frappe.db.commit()
				
				frappe.msgprint(f"Waybill created successfully: {self.waybill_number}")
			else:
				self.status = "Failed"
				self.error_message = response.get("error", "Unknown error")
				self.api_response = json.dumps(response, indent=2)
				self.save()
				frappe.throw(f"Failed to create waybill: {self.error_message}")
				
		except Exception as e:
			self.status = "Failed"
			self.error_message = str(e)
			self.save()
			frappe.throw(f"Error creating waybill: {str(e)}")
	
	def update_tracking(self):
		"""Update tracking information from Courier Guy API"""
		if not self.tracking_number:
			frappe.throw("No tracking number available")
		
		try:
			api = CourierGuyAPI()
			tracking_data = api.get_tracking(self.tracking_number)
			
			if tracking_data.get("success"):
				self.tracking_history = json.dumps(tracking_data.get("history", []), indent=2)
				self.last_tracking_update = frappe.utils.now()
				
				# Update status based on tracking
				latest_status = tracking_data.get("status", "").lower()
				if "delivered" in latest_status:
					self.status = "Delivered"
				elif "in transit" in latest_status or "picked up" in latest_status:
					self.status = "In Transit"
				
				self.save()
				frappe.db.commit()
				
				return tracking_data
			else:
				frappe.throw(f"Failed to get tracking: {tracking_data.get('error', 'Unknown error')}")
				
		except Exception as e:
			frappe.throw(f"Error getting tracking: {str(e)}")
	
	def print_waybill(self):
		"""Get waybill print URL"""
		if not self.waybill_number:
			frappe.throw("Waybill not created yet")
		
		try:
			api = CourierGuyAPI()
			print_data = api.get_waybill_print(self.waybill_number)
			
			if print_data.get("success"):
				return print_data.get("print_url") or print_data.get("pdf_url")
			else:
				frappe.throw(f"Failed to get print URL: {print_data.get('error', 'Unknown error')}")
				
		except Exception as e:
			frappe.throw(f"Error getting print URL: {str(e)}")


@frappe.whitelist()
def create_waybill_from_delivery_note(delivery_note):
	"""Create waybill from delivery note"""
	dn = frappe.get_doc("Delivery Note", delivery_note)
	
	# Check if waybill already exists
	existing = frappe.db.exists("Courier Guy Waybill", {"delivery_note": delivery_note})
	if existing:
		frappe.throw("Waybill already exists for this Delivery Note")
	
	# Create waybill
	waybill = frappe.get_doc({
		"doctype": "Courier Guy Waybill",
		"delivery_note": delivery_note,
		"customer": dn.customer,
		"status": "Draft"
	})
	
	waybill.insert()
	
	# Submit to create waybill via API
	waybill.submit()
	
	return waybill.name


@frappe.whitelist()
def update_tracking_status(waybill_name):
	"""Update tracking status for a waybill"""
	waybill = frappe.get_doc("Courier Guy Waybill", waybill_name)
	waybill.update_tracking()
	return waybill.status


@frappe.whitelist()
def get_waybill_print_url(waybill_name):
	"""Get print URL for waybill"""
	waybill = frappe.get_doc("Courier Guy Waybill", waybill_name)
	return waybill.print_waybill()

