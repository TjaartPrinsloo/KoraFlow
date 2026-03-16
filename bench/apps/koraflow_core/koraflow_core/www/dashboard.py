import frappe
from frappe import _
import json
from frappe.utils import add_days, getdate, date_diff, flt

def get_context(context):
	"""
	Load context for Patient Dashboard including Vitals and Refill Info.
	"""
	context.no_cache = 1

	# Set defaults so template never crashes on undefined
	context.patient = None
	context.alerts = []
	context.refill_info = None
	context.vitals_history = []
	context.latest_vital = None
	context.weight_change = 0
	context.vitals_chart_data = "[]"
	context.bmi_class = "Unknown"
	context.bmi_badge_color = "gray-200"
	context.bmi_percent = 50
	context.target_weight = 70
	context.progress_percent = 0
	context.intake_completed = False

	# 1. Access Control
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to view the dashboard"), frappe.PermissionError)

	# Check if user is Patient or Sales Agent
	roles = frappe.get_roles()
	if "Patient" not in roles:
		if "Sales Agent" in roles:
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/sales_agent_dashboard"
			raise frappe.Redirect
		else:
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/app/home"
			raise frappe.Redirect

	# Get Patient Doc
	patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	if not patient_name:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/glp1-intake"
		raise frappe.Redirect

	patient = frappe.get_doc("Patient", patient_name)
	context.patient = patient
	
	# 2. Alerts Logic
	context.alerts = []
	intake_forms = frappe.get_all("GLP-1 Intake Submission", filters={"patient": patient.name}, limit=1, ignore_permissions=True)
	allow_retake = getattr(patient, 'custom_allow_intake_retake', 0)
	context.intake_completed = bool(intake_forms) and not allow_retake
	
	if not context.intake_completed:
		context.alerts.append({
			"type": "warning", 
			"title": "Intake Incomplete",
			"message": "Please complete your GLP-1 intake to get your prescription.",
			"action": "go_to_intake"
		})

	# Reminder to log vitals
	last_vital = frappe.db.get_value("Patient Vital", {"patient": patient.name}, "date", order_by="date desc")
	if not last_vital or date_diff(getdate(), getdate(last_vital)) > 7:
		context.alerts.append({
			"type": "info",
			"title": "Log Your Weekly Weight",
			"message": "It's been a while since your last log. Tracking helps us adjust your plan.",
			"action": "log_vitals"
		})

	# 3. Refill Info
	# Only show Active Plan if patient is Active AND intake is complete
	if patient.status == "Disabled" or not context.intake_completed:
		context.refill_info = None
	else:
		# Fetch active prescription details
		try:
			# Define active statuses (exclude Draft)
			active_statuses = ["Dispensed", "Shipped", "Delivered", "Dispense Queued", "Active", "Quoted", "Doctor Approved"]
			
			active_rx = frappe.db.get_value("GLP-1 Patient Prescription", 
				{"patient": patient.name, "status": ["in", active_statuses]}, 
				["name", "medication", "dosage", "refill_due_date", "current_cycle", "number_of_repeats_allowed"], as_dict=True)
			
			if active_rx:
				# Cycles logic: total = allowed repeats + 1 (the initial dispense)
				total_cycles = (active_rx.get('number_of_repeats_allowed') or 0) + 1
				current_cycle = active_rx.get('current_cycle') or 0
				
				# Refill logic
				refill_due_date = active_rx.get('refill_due_date')
				days_until_refill = None
				if refill_due_date:
					days_until_refill = date_diff(getdate(refill_due_date), getdate())
				
				context.refill_info = active_rx
				context.refill_info['total_cycles'] = total_cycles
				context.refill_info['current_cycle'] = current_cycle
				context.refill_info['refill_due_date'] = refill_due_date
				context.refill_info['days_until_refill'] = days_until_refill
				
				# Plan is "active" if there are repeats left OR it's a one-time dispense that hasn't finished yet
				context.refill_info['has_repeats_remaining'] = current_cycle < total_cycles
				context.refill_info['is_one_time_plan'] = total_cycles == 1
				context.refill_info['status'] = "Active"
			else:
				context.refill_info = None
		except Exception:
			context.refill_info = None


	# 4. Vitals Data
	vitals = frappe.get_all("Patient Vital", 
		filters={"patient": patient.name}, 
		fields=["name", "date", "weight_kg", "bmi", "height_cm"],
		order_by="date asc"
	)
	
	context.vitals_history = vitals
	context.latest_vital = vitals[-1] if vitals else None
	
	# Weight Change
	if len(vitals) >= 2:
		context.weight_change = flt(vitals[-1].weight_kg) - flt(vitals[0].weight_kg)
	else:
		context.weight_change = 0

	# Chart Data
	chart_data = []
	for v in vitals:
		chart_data.append({
			"date": str(v.date),
			"weight": v.weight_kg
		})
	context.vitals_chart_data = json.dumps(chart_data)
	
	# BMI Visuals
	if context.latest_vital and context.latest_vital.bmi:
		bmi = flt(context.latest_vital.bmi)
		context.bmi_class = get_bmi_class(bmi)
		context.bmi_badge_color = get_bmi_color(bmi)
		context.bmi_percent = min(max((bmi - 15) / (35 - 15) * 100, 0), 100)
	else:
		context.bmi_class = "Unknown"
		context.bmi_badge_color = "gray-200"
		context.bmi_percent = 50

	# Target
	context.target_weight = getattr(patient, 'custom_target_weight', None) or 70
	
	# Progress
	if context.latest_vital and context.target_weight:
		current = flt(context.latest_vital.weight_kg)
		start = flt(vitals[0].weight_kg) if vitals else current
		target = flt(context.target_weight)
		
		if start != target:
			progress = ((start - current) / (start - target)) * 100
			context.progress_percent = max(0, min(progress, 100))
		else:
			context.progress_percent = 100
	else:
		context.progress_percent = 0

	context.show_billing = True
	context.show_medical_auth = True
	context.title = _("Dashboard")

def get_bmi_class(bmi):
	if bmi < 18.5: return "Underweight"
	if bmi < 25: return "Normal"
	if bmi < 30: return "Overweight"
	return "Obese"

def get_bmi_color(bmi):
	if bmi < 18.5: return "yellow-200"
	if bmi < 25: return "green-200"
	if bmi < 30: return "orange-200"
	return "red-200"

@frappe.whitelist()
def submit_vital(weight, height=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login"))
		
	patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
	if not patient_name:
		frappe.throw(_("Patient not found"))

	# Create Vital Entry
	doc = frappe.get_doc({
		"doctype": "Patient Vital",
		"patient": patient_name,
		"date": frappe.utils.nowdate(),
		"weight_kg": flt(weight),
		"height_cm": flt(height)
	})
	
	if not height:
		try:
			patient_height = frappe.db.get_value("Patient", patient_name, "custom_height_cm") or \
							 frappe.db.get_value("Patient", patient_name, "intake_height_cm")
			if patient_height:
				doc.height_cm = flt(patient_height)
				height = doc.height_cm
		except Exception:
			pass
			
	# Calculate BMI if both height and weight are available
	if flt(weight) > 0 and flt(height) > 0:
		w = flt(weight)
		h = flt(height) / 100
		doc.bmi = w / (h * h)

	doc.insert(ignore_permissions=True)
	return True

