# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Batch Traceability Report
Shows complete traceability for a GLP-1 batch
"""

import frappe
from frappe import _
from koraflow_core.utils.glp1_compliance import get_batch_traceability


def execute(filters=None):
	"""Generate batch traceability report"""
	if not filters:
		filters = {}
	
	batch_name = filters.get("batch")
	if not batch_name:
		return [], []
	
	# Get traceability data
	trace_data = get_batch_traceability(batch_name)
	
	if "error" in trace_data:
		return [], []
	
	columns = [
		{"fieldname": "event_type", "label": _("Event Type"), "fieldtype": "Data", "width": 150},
		{"fieldname": "event_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "document", "label": _("Document"), "fieldtype": "Dynamic Link", "options": "doctype", "width": 150},
		{"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 150},
		{"fieldname": "actor", "label": _("Actor"), "fieldtype": "Link", "options": "User", "width": 150},
		{"fieldname": "details", "label": _("Details"), "fieldtype": "Data", "width": 200}
	]
	
	data = []
	
	# Add compounding records
	for comp in trace_data.get("compounding_records", []):
		data.append({
			"event_type": "Compounding",
			"event_date": comp.get("compound_date"),
			"document": comp.get("name"),
			"doctype": "GLP-1 Compounding Record",
			"patient": comp.get("patient"),
			"actor": comp.get("responsible_pharmacist"),
			"details": f"Quantity: {comp.get('compound_quantity')}"
		})
	
	# Add dispense confirmations
	for dispense in trace_data.get("dispense_confirmations", []):
		data.append({
			"event_type": "Dispense",
			"event_date": None,  # Get from document
			"document": dispense.get("name"),
			"doctype": "GLP-1 Dispense Confirmation",
			"patient": dispense.get("patient"),
			"actor": dispense.get("pharmacist"),
			"details": f"Prescription: {dispense.get('prescription')}"
		})
	
	# Add stock entries
	for stock_entry in trace_data.get("stock_entries", []):
		data.append({
			"event_type": "Stock Movement",
			"event_date": stock_entry.get("posting_date"),
			"document": stock_entry.get("name"),
			"doctype": "Stock Entry",
			"patient": None,
			"actor": None,
			"details": f"Purpose: {stock_entry.get('purpose')}"
		})
	
	# Add cold chain logs
	for log in trace_data.get("cold_chain_logs", []):
		data.append({
			"event_type": "Cold Chain Check",
			"event_date": log.get("check_time"),
			"document": None,
			"doctype": None,
			"patient": None,
			"actor": None,
			"details": f"Temp: {log.get('temperature')}°C, Excursion: {log.get('excursion')}"
		})
	
	return columns, data
