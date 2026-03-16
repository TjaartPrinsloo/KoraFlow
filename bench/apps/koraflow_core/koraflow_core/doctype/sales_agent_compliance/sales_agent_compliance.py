# Copyright (c) 2026, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class SalesAgentCompliance(Document):
	def validate(self):
		"""Validate compliance status before saving"""
		self.update_compliance_status()
	
	def update_compliance_status(self):
		"""Update overall compliance status based on individual acceptances"""
		if (self.popia_agreement_accepted and 
		    self.sahpra_guidelines_accepted and 
		    self.code_of_conduct_accepted):
			self.compliance_status = "Compliant"
		else:
			self.compliance_status = "Pending"
		
		# Update audit date
		self.last_audit_date = frappe.utils.now()
	
	def accept_document(self, document_type, version, ip_address=None):
		"""
		Accept a compliance document
		
		Args:
			document_type: 'POPIA', 'SAHPRA', or 'Code of Conduct'
			version: Version string (e.g., "2.1.0")
			ip_address: IP address of the user accepting
		"""
		if not ip_address:
			ip_address = frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else '0.0.0.0'
		
		now = frappe.utils.now()
		
		if document_type == "POPIA":
			self.popia_agreement_accepted = 1
			self.popia_agreement_version = version
			self.popia_accepted_date = now
			self.popia_accepted_ip = ip_address
		elif document_type == "SAHPRA":
			self.sahpra_guidelines_accepted = 1
			self.sahpra_guidelines_version = version
			self.sahpra_accepted_date = now
			self.sahpra_accepted_ip = ip_address
		elif document_type == "Code of Conduct":
			self.code_of_conduct_accepted = 1
			self.code_of_conduct_version = version
			self.code_of_conduct_accepted_date = now
			self.code_of_conduct_accepted_ip = ip_address
		
		self.update_compliance_status()
		self.save()
		
		frappe.logger().info(
			f"Sales Agent {self.sales_agent} accepted {document_type} "
			f"version {version} from IP {ip_address}"
		)


@frappe.whitelist()
def get_compliance_status(user=None):
	"""Get compliance status for a sales agent"""
	if not user:
		user = frappe.session.user
	
	# Check if compliance record exists
	compliance = frappe.db.get_value(
		"Sales Agent Compliance",
		{"sales_agent": user},
		["compliance_status", "popia_agreement_accepted", "sahpra_guidelines_accepted", 
		 "code_of_conduct_accepted", "popia_agreement_version", "sahpra_guidelines_version",
		 "code_of_conduct_version"],
		as_dict=True
	)
	
	if not compliance:
		# Create new compliance record
		doc = frappe.get_doc({
			"doctype": "Sales Agent Compliance",
			"sales_agent": user,
			"compliance_status": "Pending"
		})
		doc.insert(ignore_permissions=True)
		
		return {
			"status": "Pending",
			"popia_accepted": False,
			"sahpra_accepted": False,
			"conduct_accepted": False
		}
	
	return {
		"status": compliance.compliance_status,
		"popia_accepted": compliance.popia_agreement_accepted,
		"sahpra_accepted": compliance.sahpra_guidelines_accepted,
		"conduct_accepted": compliance.code_of_conduct_accepted,
		"popia_version": compliance.popia_agreement_version,
		"sahpra_version": compliance.sahpra_guidelines_version,
		"conduct_version": compliance.code_of_conduct_version
	}


@frappe.whitelist()
def accept_document(document_type, version):
	"""
	Accept a compliance document
	
	Args:
		document_type: 'POPIA', 'SAHPRA', or 'Code of Conduct'
		version: Version string
	"""
	user = frappe.session.user
	ip_address = frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else '0.0.0.0'
	
	# Get or create compliance record
	compliance_name = frappe.db.get_value("Sales Agent Compliance", {"sales_agent": user})
	
	if compliance_name:
		compliance = frappe.get_doc("Sales Agent Compliance", compliance_name)
	else:
		compliance = frappe.get_doc({
			"doctype": "Sales Agent Compliance",
			"sales_agent": user
		})
		compliance.insert(ignore_permissions=True)
	
	# Accept the document
	compliance.accept_document(document_type, version, ip_address)
	
	return {
		"success": True,
		"message": f"{document_type} accepted successfully",
		"compliance_status": compliance.compliance_status
	}
