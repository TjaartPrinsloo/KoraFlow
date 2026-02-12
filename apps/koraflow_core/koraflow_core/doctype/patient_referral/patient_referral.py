# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class PatientReferral(Document):
	def autoname(self):
		"""Set referral_id from naming series"""
		if not self.referral_id:
			from frappe.model.naming import make_autoname
			self.referral_id = make_autoname(self.naming_series + ".#####")
			self.name = self.referral_id

	def validate(self):
		"""Validate referral data"""
		# Ensure patient name fields are populated if patient is set
		if self.patient and not self.patient_first_name:
			self._fetch_patient_data()
		
		# Update patient name display
		if self.patient_first_name or self.patient_last_name:
			self.patient_name_display = f"{self.patient_first_name or ''} {self.patient_last_name or ''}".strip()
		
		# Update last status update timestamp
		if self.has_value_changed("current_journey_status"):
			self.last_status_update = frappe.utils.now()

	def before_insert(self):
		"""Set initial values"""
		if not self.referral_date:
			self.referral_date = frappe.utils.today()
		if not self.current_journey_status:
			self.current_journey_status = "Lead Received"
		if not self.last_status_update:
			self.last_status_update = frappe.utils.now()

	def on_update(self):
		"""Handle status changes and commission updates"""
		# Update commission when invoice is paid
		if self.current_journey_status == "Invoice Paid":
			self._update_commission()
		
		# Link to Sales Partner if sales agent has one
		if self.sales_agent and not self.sales_partner:
			self._link_sales_partner()

	def _fetch_patient_data(self):
		"""Fetch safe patient metadata (name only, no medical data)"""
		if not self.patient:
			return
		
		try:
			patient = frappe.get_doc("Patient", self.patient)
			self.patient_first_name = patient.first_name or ""
			self.patient_last_name = patient.last_name or ""
			self.patient_name_display = patient.patient_name or ""
		except frappe.DoesNotExistError:
			frappe.msgprint(_("Patient not found"), indicator="orange")

	def _link_sales_partner(self):
		"""Link referral to Sales Partner for commission tracking"""
		if not self.sales_agent:
			return
		
		# Check if user has a linked Sales Partner
		user = frappe.get_doc("User", self.sales_agent)
		if hasattr(user, 'sales_partner') and user.sales_partner:
			self.sales_partner = user.sales_partner
		else:
			# Try to find Sales Partner by user email or name
			filters = {}
			if frappe.db.has_column("Sales Partner", "email_id"):
				filters["email_id"] = user.email or user.name
			elif frappe.db.has_column("Sales Partner", "email"):
				filters["email"] = user.email or user.name
			
			if filters:
				sales_partner = frappe.db.get_value("Sales Partner", filters, "name")
				if sales_partner:
					self.sales_partner = sales_partner

	def _update_commission(self):
		"""Calculate and update commission when invoice is paid"""
		if not self.sales_partner:
			return
		
		# Find related Sales Invoice
		sales_invoice = frappe.db.get_value(
			"Sales Invoice",
			{
				"patient": self.patient,
				"sales_partner": self.sales_partner,
				"docstatus": 1,
				"status": "Paid"
			},
			["name", "total_commission", "grand_total"],
			as_dict=True
		)
		
		if sales_invoice:
			self.total_commission = sales_invoice.total_commission or 0
			self.commission_status = "Approved"
			
			# Create Commission Record
			from koraflow_core.koraflow_core.doctype.commission_record.commission_record import create_commission_from_invoice
			create_commission_from_invoice(sales_invoice.name, self.name)
			
			# Check if commission is already paid
			commission_paid = frappe.db.get_value(
				"Sales Partner Commission",
				{
					"sales_invoice": sales_invoice.name,
					"status": "Paid"
				},
				"name"
			)
			
			if commission_paid:
				self.commission_status = "Paid"
				paid_date = frappe.db.get_value(
					"Sales Partner Commission",
					commission_paid,
					"paid_date"
				)
				if paid_date:
					self.commission_paid_date = paid_date


@frappe.whitelist()
def update_referral_status(referral_id, new_status):
	"""Update referral status (called by sales team)"""
	referral = frappe.get_doc("Patient Referral", referral_id)
	
	# Validate status transition
	valid_statuses = [
		"Lead Received",
		"Contacted by Sales",
		"Consultation Scheduled",
		"Consultation Completed",
		"Prescription Issued",
		"Awaiting Payment",
		"Invoice Paid",
		"Medication Dispatched",
		"Completed",
		"Cancelled"
	]
	
	if new_status not in valid_statuses:
		frappe.throw(_("Invalid status: {0}").format(new_status))
	
	referral.current_journey_status = new_status
	referral.last_status_update = frappe.utils.now()
	referral.save(ignore_permissions=True)
	
	return {"status": "success", "message": _("Status updated successfully")}


@frappe.whitelist()
def get_agent_referrals(agent=None):
	"""Get all referrals for a sales agent"""
	if not agent:
		agent = frappe.session.user
	
	# Apply permission filters
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"sales_agent": agent},
		fields=[
			"name",
			"referral_id",
			"patient_first_name",
			"patient_last_name",
			"patient_name_display",
			"referral_date",
			"current_journey_status",
			"last_status_update",
			"assigned_sales_team_member",
			"agent_notes",
			"commission_status",
			"total_commission"
		],
		order_by="referral_date desc"
	)
	
	return referrals


@frappe.whitelist()
def fetch_patient_names(patient):
	"""Fetch patient names (safe metadata only)"""
	if not patient:
		return {}
	
	try:
		patient_doc = frappe.get_doc("Patient", patient)
		return {
			"first_name": patient_doc.first_name or "",
			"last_name": patient_doc.last_name or "",
			"patient_name": patient_doc.patient_name or ""
		}
	except frappe.DoesNotExistError:
		return {}


@frappe.whitelist()
def get_sales_partner_for_agent(agent):
	"""Get Sales Partner linked to agent"""
	if not agent:
		return None
	
	# Check if user has a linked Sales Partner
	user = frappe.get_doc("User", agent)
	if hasattr(user, 'sales_partner') and user.sales_partner:
		return user.sales_partner
	
	# Try to find Sales Partner by user email or name
	sales_partner = frappe.db.get_value(
		"Sales Partner",
		{"email_id": user.email or user.name},
		"name"
	)
	
	return sales_partner


def update_referral_on_invoice_paid(doc, method):
	"""Update referral status when Sales Invoice is paid"""
	if doc.doctype != "Sales Invoice":
		return
	
	# Check if invoice is paid
	if doc.status != "Paid" or doc.docstatus != 1:
		return
	
	# Find related referral
	if not doc.patient:
		return
	
	# Also check by sales_partner if available
	filters = {"patient": doc.patient, "current_journey_status": ["!=", "Completed"]}
	if doc.sales_partner:
		filters["sales_partner"] = doc.sales_partner
	
	referrals = frappe.get_all(
		"Patient Referral",
		filters=filters,
		fields=["name"]
	)
	
	for ref in referrals:
		referral = frappe.get_doc("Patient Referral", ref.name)
		
		# Update status if invoice is paid
		if referral.current_journey_status != "Invoice Paid":
			referral.current_journey_status = "Invoice Paid"
			referral.last_status_update = frappe.utils.now()
			referral._update_commission()
			referral.save(ignore_permissions=True)


def sync_patient_name_to_referrals(doc, method):
	"""Sync patient name changes to referrals (safe metadata only)"""
	if doc.doctype != "Patient":
		return
	
	# Update all referrals for this patient
	referrals = frappe.get_all(
		"Patient Referral",
		filters={"patient": doc.name},
		fields=["name"]
	)
	
	for ref in referrals:
		referral = frappe.get_doc("Patient Referral", ref.name)
		referral.patient_first_name = doc.first_name or ""
		referral.patient_last_name = doc.last_name or ""
		referral.patient_name_display = doc.patient_name or ""
		referral.save(ignore_permissions=True)

