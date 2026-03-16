# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today, add_days, getdate


def parse_duration_to_days(duration_str):
	"""Parse duration string like '1 Month', '2 Weeks' to number of days"""
	if not duration_str:
		return 30  # Default to 1 month
	
	duration_str = duration_str.strip().lower()
	
	# Common patterns
	if "month" in duration_str:
		try:
			months = int(duration_str.split()[0])
			return months * 30
		except (ValueError, IndexError):
			return 30
	elif "week" in duration_str:
		try:
			weeks = int(duration_str.split()[0])
			return weeks * 7
		except (ValueError, IndexError):
			return 7
	elif "day" in duration_str:
		try:
			days = int(duration_str.split()[0])
			return days
		except (ValueError, IndexError):
			return 30
	else:
		# Try to parse as number directly
		try:
			return int(duration_str)
		except ValueError:
			return 30  # Default to 1 month


class GLP1DispenseConfirmation(Document):
	def validate(self):
		"""Validate dispense confirmation"""
		if not self.patient_acknowledgment:
			frappe.throw(_("Patient acknowledgment is required"))
		
		# Verify stock entry exists and is submitted
		if self.stock_entry:
			stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
			if stock_entry.docstatus != 1:
				frappe.throw(_("Stock Entry must be submitted before confirmation"))
	
	def on_submit(self):
		"""Update prescription status, track cycles, and create audit log"""
		# Update prescription status and cycle tracking
		if self.prescription:
			prescription = frappe.get_doc("GLP-1 Patient Prescription", self.prescription)
			
			# Update status
			prescription.status = "Dispensed"
			
			# Track cycle (increment dispense count)
			prescription.current_cycle = (prescription.current_cycle or 0) + 1
			prescription.last_dispense_date = today()
			
			# Calculate next refill date based on duration
			duration_days = parse_duration_to_days(prescription.duration)
			prescription.refill_due_date = add_days(getdate(today()), duration_days)
			
			# Reset renewal quote flag for next cycle
			prescription.renewal_quote_generated = 0
			
			prescription.save(ignore_permissions=True)
			
			frappe.msgprint(
				_("Prescription cycle {0} of {1} dispensed. Next refill due: {2}").format(
					prescription.current_cycle,
					(prescription.number_of_repeats_allowed or 0) + 1,
					frappe.format_date(prescription.refill_due_date)
				),
				indicator="green"
			)
		
		# Create audit log
		from koraflow_core.utils.glp1_compliance import create_audit_log
		create_audit_log(
			event_type="Dispense",
			reference_doctype="GLP-1 Dispense Confirmation",
			reference_name=self.name,
			patient=self.patient,
			actor=self.pharmacist,
			details={
				"batch": self.batch,
				"stock_entry": self.stock_entry,
				"patient_acknowledged": self.patient_acknowledgment
			}
		)
