"""
My Treatment Page
"""
import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access this page"), frappe.PermissionError)
	
	if "Patient" not in frappe.get_roles():
		frappe.throw(_("Access denied"), frappe.PermissionError)
	
	patient = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	
	if not patient:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/glp1-intake"
		return
	
	context.patient = frappe.get_doc("Patient", patient)
	
	# Get Prescriptions - wrap in try-except for permission/schema issues
	try:
		context.prescriptions = frappe.get_all(
			"GLP-1 Patient Prescription",
			filters={"patient": patient},
			fields=["name", "medication", "dosage", "status", "prescription_date", "duration", "doctor", "doctor_registration_number"],
			order_by="prescription_date desc"
		)
		
		# Filter out medications that are dispensed in-house
		# These should NOT be visible to patients per SAHPRA regulations
		# Patients could take them to external pharmacies otherwise
		try:
			in_house_meds = frappe.get_all(
				"Medication",
				filters={"custom_dispensed_in_house": 1},
				pluck="name"
			)
			# Only keep prescriptions for external pharmacy meds (not dispensed in-house)
			context.prescriptions = [
				p for p in context.prescriptions 
				if p.medication not in in_house_meds
			]
		except Exception:
			# Fallback: if custom field doesn't exist yet, use hardcoded list
			s4_meds = ["Ozempic", "Wegovy", "Mounjaro", "Zepbound", "Saxenda", "Rybelsus", 
					   "Titanium", "PreZion", "Semaglutide", "Tirzepatide", "Liraglutide"]
			context.prescriptions = [
				p for p in context.prescriptions 
				if not any(med.lower() in str(p.medication).lower() for med in s4_meds)
			]
	except Exception:
		context.prescriptions = []
	
	# Get Shipments (for tracking) - wrap in try-except
	try:
		context.shipments = frappe.get_all(
			"GLP-1 Shipment",
			filters={"patient": patient},
			fields=["name", "status", "courier_reference", "tracking_url", "delivery_date", "creation", "waybill_number", "actual_delivery"],
			order_by="creation desc",
			limit=5
		)
	except Exception:
		context.shipments = []
	
	# Get Pending Quotations
	customer = frappe.db.get_value("Patient", patient, "customer")
	if customer:
		context.quotations = frappe.get_all(
			"Quotation",
			filters={"party_name": customer, "docstatus": 0, "status": "Open"},
			fields=["name", "total", "transaction_date", "currency", "grand_total"],
			order_by="transaction_date desc"
		)
	else:
		context.quotations = []

	# Active Prescription (Latest one that is not closed/expired)
	context.active_prescription = None
	if context.prescriptions:
		for p in context.prescriptions:
			if p.status not in ["Expired", "Closed", "Draft"]:
				context.active_prescription = p
				break

	# Refill Info for Active Plan widget in sidebar
	context.refill_info = None
	try:
		from frappe.utils import date_diff, today, getdate
		
		# Get the most recent active prescription with cycle info
		active_rx = frappe.get_all(
			"GLP-1 Patient Prescription",
			filters={
				"patient": patient,
				"status": ["in", ["Dispensed", "Shipped", "Delivered", "Quoted", "Dispense Queued", "Active"]]
			},
			fields=[
				"name", "medication", "dosage", "number_of_repeats_allowed", 
				"current_cycle", "refill_due_date", "last_dispense_date", "status"
			],
			order_by="last_dispense_date desc",
			limit=1
		)
		
		if active_rx:
			rx = active_rx[0]
			total_cycles = (rx.number_of_repeats_allowed or 0) + 1
			days_until_refill = None
			
			if rx.refill_due_date:
				days_until_refill = date_diff(getdate(rx.refill_due_date), getdate(today()))
			
			context.refill_info = {
				"prescription_name": rx.name,
				"medication": rx.medication,
				"dosage": rx.dosage,
				"current_cycle": rx.current_cycle or 1,
				"total_cycles": total_cycles,
				"refill_due_date": rx.refill_due_date,
				"days_until_refill": days_until_refill,
				"status": rx.status,
				"has_repeats_remaining": (rx.current_cycle or 0) < total_cycles
			}
	except Exception:
		# If doctype doesn't exist or fields missing, skip gracefully
		pass
