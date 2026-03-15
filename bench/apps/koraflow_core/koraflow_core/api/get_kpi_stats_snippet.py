
@frappe.whitelist()
def get_kpi_stats(agent):
	"""Calculate KPI statistics for the agent"""
	# 1. New Referrals (This Week)
	# default to 0 for now or calculate if needed. The UI has "+3 this week" hardcoded, maybe we make that dynamic too?
	# For now, let's get total referrals count?
	# The UI shows "New Refs" as a count. "stat-referrals" usually gets referrals.length. 
	# Actually the UI code sets stat-referrals to referrals.length which is limit 10 in API. 
	# We should probably get a proper count.
	
	total_referrals = frappe.db.count("Patient Referral", {"sales_agent": agent})
	
	# 2. Conversion Rate
	# Count referrals with status 'Converted' or similar journey end states (Prescription Issued, Invoice Paid etc)
	# Let's consider distinct patients who have placed an order (Sales Invoice)
	# Or simplified: Status in ["Prescription Issued", "Invoice Paid", "Medication Dispatched", "Completed"]
	converted_count = frappe.db.count("Patient Referral", {
		"sales_agent": agent,
		"current_journey_status": ["in", ["Prescription Issued", "Invoice Paid", "Medication Dispatched", "Completed", "Converted"]]
	})
	
	conversion_rate = 0
	if total_referrals > 0:
		conversion_rate = (converted_count / total_referrals) * 100
		
	# 3. Total Patients
	# Count distinct patients linked to this agent
	# Can use Patient Referral count if 1:1, or count Patients where custom_sales_agent = agent
	# Let's use Patient Referral unique patients
	total_patients = frappe.db.count("Patient Referral", {"sales_agent": agent}) 
	# (Assuming 1 referral per patient for now, or just use total referrals as proxy)
	
	# 4. Avg Ticket
	# Average grand_total of Paid Sales Invoices linked to patients of this agent
	# This is a bit complex SQL.
	avg_ticket = 0
	
	# Get all patient names for this agent
	patient_names = frappe.get_all("Patient Referral", filters={"sales_agent": agent}, pluck="patient")
	
	if patient_names:
		# Get average invoice amount for these patients
		# Invoice links to Patient via 'patient' field
		result = frappe.db.sql("""
			SELECT AVG(grand_total) 
			FROM `tabSales Invoice` 
			WHERE patient IN %(patients)s 
			AND status = 'Paid'
		""", {"patients": patient_names})
		
		if result and result[0][0]:
			avg_ticket = result[0][0]
			
	return {
		"total_referrals": total_referrals,
		"conversion_rate": round(conversion_rate, 1),
		"total_patients": total_patients,
		"avg_ticket": round(avg_ticket, 2)
	}
