# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Prescription Renewal Scheduler Job

This module handles automatic generation of renewal quotes for GLP-1 prescriptions.
Runs daily at 6 AM to check for prescriptions due within 7 workdays.
"""

import frappe
from frappe import _
from frappe.utils import today, getdate, add_days, date_diff


def add_workdays(start_date, num_days):
	"""Add workdays (Mon-Fri) to a date"""
	current = getdate(start_date)
	days_added = 0
	
	while days_added < num_days:
		current = add_days(current, 1)
		# Skip weekends (5 = Saturday, 6 = Sunday)
		if current.weekday() < 5:
			days_added += 1
	
	return current


def is_previous_invoice_paid(prescription_name):
	"""Check if the patient's previous invoice for this prescription is paid"""
	# Get the linked quotation to find customer
	prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
	
	if not prescription.linked_quotation:
		return True  # No previous quote, allow
	
	# Get customer from quotation
	customer = frappe.db.get_value("Quotation", prescription.linked_quotation, "party_name")
	if not customer:
		return True
	
	# Check for any outstanding invoices for this customer
	outstanding_invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"custom_prescription": prescription_name
		},
		limit=1
	)
	
	# If there are outstanding invoices, previous is NOT paid
	return len(outstanding_invoices) == 0


def create_renewal_quotation(prescription_name):
	"""Create a renewal quotation based on the existing prescription"""
	try:
		prescription = frappe.get_doc("GLP-1 Patient Prescription", prescription_name)
		
		# Get patient's customer link
		customer = frappe.db.get_value("Patient", prescription.patient, "customer")
		if not customer:
			frappe.log_error(
				title="Quotation Job", 
				message=f"No customer for patient {prescription.patient}"
			)
			return None
		
		# Get medication item
		medication = frappe.get_doc("Medication", prescription.medication)
		
		# Find the linked item from medication
		item_code = None
		if medication.linked_items:
			for linked_item in medication.linked_items:
				item_code = linked_item.item
				break
		
		if not item_code:
			frappe.log_error(
				title="Quotation Job", 
				message=f"No item for medication {prescription.medication}"
			)
			return None
		
		# Get item details for pricing
		item = frappe.get_doc("Item", item_code)
		
		# Get selling price
		from erpnext.stock.get_item_details import get_price_list_rate
		price = get_price_list_rate({
			"price_list": frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling",
			"item_code": item_code,
			"customer": customer,
			"qty": prescription.quantity or 1
		})
		
		rate = price or item.standard_rate or 0
		
		# Create renewal quotation
		quotation = frappe.get_doc({
			"doctype": "Quotation",
			"party_name": customer,
			"quotation_to": "Customer",
			"order_type": "Sales",
			"transaction_date": today(),
			"custom_prescription": prescription_name,
			"items": [{
				"item_code": item_code,
				"qty": prescription.quantity or 1,
				"rate": rate,
				"custom_prescription": prescription_name
			}]
		})
		
		quotation.insert(ignore_permissions=True)
		quotation.submit()
		
		# Update prescription
		frappe.db.set_value("GLP-1 Patient Prescription", prescription_name, {
			"renewal_quote_generated": 1,
			"linked_quotation": quotation.name,
			"status": "Quoted"
		})
		
		frappe.logger().info(f"Created renewal quotation {quotation.name} for prescription {prescription_name}")
		
		return quotation.name
	
	except Exception as e:
		frappe.log_error(
			title="Quotation Job", 
			message=f"Error creating renewal quotation for {prescription_name}: {str(e)}"
		)
		return None


def send_renewal_notification(patient_name, quotation_name):
	"""Send email notification to patient about renewal quote"""
	try:
		patient = frappe.get_doc("Patient", patient_name)
		
		if not patient.email:
			frappe.logger().info(f"No email for patient {patient_name}, skipping notification")
			return
		
		# Send email
		frappe.sendmail(
			recipients=[patient.email],
			subject=_("Your GLP-1 Medication Renewal Quote is Ready"),
			message=_("""
<p>Dear {0},</p>

<p>Your prescription renewal is due soon. We have prepared a quotation for your next supply of medication.</p>

<p>Please log in to your patient portal to review and accept the quote:</p>
<p><a href="/my_treatment">View Your Treatment Dashboard</a></p>

<p>If you have any questions, please contact our support team.</p>

<p>Best regards,<br>
Slim2Well Care Team</p>
			""").format(patient.patient_name),
			delayed=True
		)
		
		frappe.logger().info(f"Sent renewal notification to {patient.email} for quote {quotation_name}")
	
	except Exception as e:
		frappe.log_error(title="Prescription Renewal Error", message=f"Error sending renewal notification to {patient_name}: {str(e)}")


def generate_renewal_quotes():
	"""
	Daily scheduler job: Check for prescriptions due within 7 workdays
	and generate renewal quotes.
	
	Conditions:
	- Status is "Delivered" (previous cycle completed)
	- Refill due date is within 7 workdays
	- Current cycle < number_of_repeats_allowed + 1 (repeats remaining)
	- Auto-renewal enabled
	- Renewal quote not already generated for this cycle
	- Previous invoice is paid
	"""
	frappe.logger().info("Starting prescription renewal quote generation")
	
	# Calculate the threshold date (7 workdays from now)
	threshold_date = add_workdays(today(), 7)
	
	# Get prescriptions needing renewal
	prescriptions = frappe.get_all(
		"GLP-1 Patient Prescription",
		filters={
			"status": "Delivered",  # Previous cycle completed
			"refill_due_date": ["<=", threshold_date],
			"auto_renewal_enabled": 1,
			"renewal_quote_generated": 0,
		},
		fields=["name", "patient", "number_of_repeats_allowed", "current_cycle"]
	)
	
	quotes_generated = 0
	
	for p in prescriptions:
		# Check if repeats remaining
		total_cycles = (p.number_of_repeats_allowed or 0) + 1
		if p.current_cycle >= total_cycles:
			frappe.logger().info(f"Prescription {p.name} has no repeats remaining ({p.current_cycle}/{total_cycles})")
			continue
		
		# Check if previous invoice paid
		if not is_previous_invoice_paid(p.name):
			frappe.logger().info(f"Previous invoice not paid for prescription {p.name}, skipping")
			continue
		
		# Generate renewal quotation
		quotation_name = create_renewal_quotation(p.name)
		
		if quotation_name:
			quotes_generated += 1
			
			# Send notification
			send_renewal_notification(p.patient, quotation_name)
	
	frappe.logger().info(f"Prescription renewal complete: {quotes_generated} quotes generated")
	frappe.db.commit()
	
	return quotes_generated
