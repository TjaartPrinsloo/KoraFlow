# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
SAHPRA Audit Report
Generates compliance audit report for SAHPRA regulations
"""

import frappe
from frappe import _
from frappe.utils import getdate, formatdate


def execute(filters=None):
	"""Generate SAHPRA audit report"""
	if not filters:
		filters = {}
	
	start_date = filters.get("start_date") or frappe.utils.add_months(frappe.utils.today(), -1)
	end_date = filters.get("end_date") or frappe.utils.today()
	
	# Get audit data
	from koraflow_core.utils.glp1_compliance import generate_sahpra_audit_report
	audit_data = generate_sahpra_audit_report(start_date, end_date)
	
	if "error" in audit_data:
		return [], []
	
	columns = [
		{"fieldname": "dispense_date", "label": _("Dispense Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 150},
		{"fieldname": "prescription", "label": _("Prescription"), "fieldtype": "Link", "options": "GLP-1 Patient Prescription", "width": 150},
		{"fieldname": "batch", "label": _("Batch"), "fieldtype": "Link", "options": "Batch", "width": 120},
		{"fieldname": "pharmacist", "label": _("Pharmacist"), "fieldtype": "Link", "options": "User", "width": 150},
		{"fieldname": "quantity", "label": _("Quantity"), "fieldtype": "Float", "width": 100},
		{"fieldname": "compounded", "label": _("Compounded"), "fieldtype": "Check", "width": 80}
	]
	
	data = []
	for dispense in audit_data.get("dispenses", []):
		# Get dispense date
		dispense_doc = frappe.get_doc("GLP-1 Dispense Confirmation", dispense.name)
		dispense_date = dispense_doc.creation.date() if dispense_doc.creation else None
		
		# Check if compounded
		compounded = frappe.db.exists(
			"GLP-1 Compounding Record",
			{"prescription": dispense.prescription}
		)
		
		# Get quantity from stock entry
		quantity = 0
		if dispense.stock_entry:
			stock_entry = frappe.get_doc("Stock Entry", dispense.stock_entry)
			for item in stock_entry.items:
				quantity += item.qty or 0
		
		data.append({
			"dispense_date": dispense_date,
			"patient": dispense.patient,
			"prescription": dispense.prescription,
			"batch": dispense.batch,
			"pharmacist": dispense.pharmacist,
			"quantity": quantity,
			"compounded": 1 if compounded else 0
		})
	
	# Add summary row
	summary = [
		_("Total Dispenses: {0}").format(audit_data.get("total_dispenses", 0)),
		_("Unique Patients: {0}").format(audit_data.get("unique_patients", 0)),
		_("Unique Pharmacists: {0}").format(audit_data.get("unique_pharmacists", 0)),
		_("Compounded: {0}").format(audit_data.get("compounded_count", 0)),
		_("Pre-packed: {0}").format(audit_data.get("pre_packed_count", 0)),
		_("Total Quantity: {0}").format(audit_data.get("total_quantity", 0))
	]
	
	return columns, data, None, summary
