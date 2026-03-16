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

	# Google Maps Settings
	google_settings = frappe.get_single("Google Settings")
	context.google_maps_api_key = google_settings.maps_api_key
	context.enable_google_maps = google_settings.enable_google_maps
	
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
		except Exception:
			# Fallback: if custom field doesn't exist yet, use hardcoded list
			in_house_meds = ["Ozempic", "Wegovy", "Mounjaro", "Zepbound", "Saxenda", "Rybelsus",
					   "Titanium", "PreZion", "Semaglutide", "Tirzepatide", "Liraglutide",
					   "Ruby Boost", "Eco Boost", "RUBY", "Gold", "Eco", "Aminowell",
					   "Wolverine Stack", "Glow Stack", "NAD+"]

		# Add in_house flag to all prescriptions
		for p in context.prescriptions:
			p.medication_in_house = 1 if p.medication in in_house_meds else 0

		# Only keep prescriptions for external pharmacy meds (not dispensed in-house)
		# NOTE: We keep them in the context for now but the UI will hide download buttons if they are in-house
		# Actually, SAHPRA says they shouldn't even be downloadable, but seeing the record is usually fine
		# unless the user explicitly wants them filtered OUT of the grid too.
		# The current logic filters them OUT of the context.prescriptions list.
		context.prescriptions = [
			p for p in context.prescriptions 
			if not p.medication_in_house
		]
	except Exception:
		context.prescriptions = []
	
	# Get Shipments (for tracking) - wrap in try-except
	try:
		context.shipments = frappe.get_all(
			"GLP-1 Shipment",
			filters={"patient": patient},
			fields=["name", "status", "courier_reference", "estimated_delivery", "creation", "waybill_number", "actual_delivery"],
			order_by="creation desc",
			ignore_permissions=True,
			limit=5
		)
	except Exception:
		context.shipments = []
	
	# Get Pending Quotations
	customer = frappe.db.get_value("Patient", patient, "customer")
	if customer:
		context.quotations = frappe.get_all(
			"Quotation",
			filters={"party_name": customer, "docstatus": 0, "status": ["in", ["Open", "Draft"]]},
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

	# Check intake status (replicate dashboard logic)
	intake_forms = frappe.get_all("GLP-1 Intake Submission", filters={"parent": patient}, limit=1)
	intake_completed = bool(intake_forms)

	# Only proceed if patient is Active AND intake is complete
	if context.patient.status != "Disabled" and intake_completed:
		try:
			from frappe.utils import date_diff, today, getdate
			
			# Get the most recent active prescription with cycle info
			active_statuses = ["Dispensed", "Shipped", "Delivered", "Dispense Queued", "Active", "Quoted", "Doctor Approved"]
			
			active_rx = frappe.get_all(
				"GLP-1 Patient Prescription",
				filters={
					"patient": patient,
					"status": ["in", active_statuses]
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
				# Cycles logic: total = allowed repeats + 1 (the initial dispense)
				total_cycles = (rx.number_of_repeats_allowed or 0) + 1
				current_cycle = rx.current_cycle or 0
				
				# Refill logic
				refill_due_date = rx.get('refill_due_date')
				days_until_refill = None
				if refill_due_date:
					from frappe.utils import today, getdate, date_diff
					days_until_refill = date_diff(getdate(refill_due_date), getdate(today()))
				
				context.refill_info = {
					"prescription_name": rx.name,
					"medication": rx.medication,
					"dosage": rx.dosage,
					"current_cycle": current_cycle,
					"total_cycles": total_cycles,
					"refill_due_date": refill_due_date,
					"days_until_refill": days_until_refill,
					"status": rx.status,
					# Plan is "active" if there are repeats left OR it's a one-time dispense that hasn't finished yet
					"has_repeats_remaining": current_cycle < total_cycles,
					"is_one_time_plan": total_cycles == 1
				}
		except Exception:
			# If doctype doesn't exist or fields missing, skip gracefully
			pass
@frappe.whitelist()
def accept_quote(quote_name, address_data=None):
	"""
	Accepts the quotation and creates the sales chain.
	Also updates patient address if provided.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to proceed"), frappe.PermissionError)

	try:
		# 1. Update Address if provided
		if address_data:
			patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
			if patient_name:
				patient = frappe.get_doc("Patient", patient_name)
				if isinstance(address_data, str):
					import json
					address_data = json.loads(address_data)
				
				if address_data.get("address_line1"):
					patient.address_line1 = address_data.get("address_line1")
				if address_data.get("city"):
					patient.city = address_data.get("city")
				if address_data.get("zip_code"):
					patient.zip_code = address_data.get("zip_code")
				
				patient.save(ignore_permissions=True)

		# 2. Handle Quotation
		quote = frappe.get_doc("Quotation", quote_name)
		
		# Save delivery notes to Quotation if provided
		if address_data and address_data.get("delivery_notes"):
			quote.custom_delivery_notes = address_data.get("delivery_notes")
			quote.db_set("custom_delivery_notes", address_data.get("delivery_notes"))
		
		# Verify ownership/permissions indirectly via party
		patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
		customer = frappe.db.get_value("Patient", patient_name, "customer")
		if quote.party_name != customer:
			frappe.throw(_("Not authorized to accept this quote"), frappe.PermissionError)

		# If Draft, submit it first
		if quote.docstatus == 0:
			quote.flags.ignore_permissions = True
			quote.submit()
			
		# 3. Trigger Sales Chain Creation (Workflow)
		# Run as Admin to bypass permission checks for creating SO/Invoice
		sales_invoice_name = None
		original_user = frappe.session.user
		frappe.set_user("Administrator")
		try:
			from koraflow_core.workflows.glp1_dispensing_workflow import create_sales_chain_from_quotation
			sales_invoice_name = create_sales_chain_from_quotation(quote)
		except Exception as e:
			# Log but don't block - the quote is already accepted
			frappe.log_error(title="My Treatment", message=f"Sales chain error (non-blocking): {str(e)}")
		finally:
			frappe.set_user(original_user)
		
		frappe.db.commit()
		return {"message": "Success", "invoice": sales_invoice_name}

	except frappe.PermissionError:
		raise
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="My Treatment", message=f"Error accepting quote: {str(e)}")
		frappe.throw(_("An error occurred while processing your request. Please try again."))

@frappe.whitelist()
def decline_quote(quote_name):
	"""
	Declines the quotation (sets status to Lost).
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to proceed"), frappe.PermissionError)
		
	try:
		quote = frappe.get_doc("Quotation", quote_name)
		
		# Verify ownership
		patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
		customer = frappe.db.get_value("Patient", patient_name, "customer")
		if quote.party_name != customer:
			frappe.throw(_("Not authorized to decline this quote"), frappe.PermissionError)
			
		# Set to Lost
		quote.status = "Lost"
		quote.save(ignore_permissions=True)
		
		return True
	except Exception as e:
		frappe.log_error(title="My Treatment", message=f"Error declining quote: {str(e)}")
		frappe.throw(_("An error occurred while processing your request."))
