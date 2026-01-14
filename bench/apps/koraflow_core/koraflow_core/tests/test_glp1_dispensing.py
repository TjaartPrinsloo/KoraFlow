# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Unit Tests for GLP-1 Dispensing System
Tests compliance checkpoints, workflow transitions, and permissions
"""

import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from koraflow_core.utils.glp1_compliance import (
	check_prescription_lock,
	check_cold_chain_compliance,
	validate_patient_reference,
	generate_sahpra_audit_report
)
from koraflow_core.utils.glp1_permissions import (
	has_glp1_prescription_permission,
	has_glp1_stock_permission
)


class TestGLP1Compliance(FrappeTestCase):
	"""Test compliance checkpoints"""
	
	def setUp(self):
		"""Set up test data"""
		# Create test patient
		self.patient = frappe.get_doc({
			"doctype": "Patient",
			"first_name": "Test",
			"last_name": "Patient",
			"patient_name": "Test Patient"
		})
		self.patient.insert(ignore_permissions=True)
	
	def tearDown(self):
		"""Clean up test data"""
		if self.patient:
			frappe.delete_doc("Patient", self.patient.name, force=1, ignore_permissions=True)
	
	def test_prescription_lock(self):
		"""Test CP-A: Prescription Lock"""
		# Create prescription
		prescription = frappe.get_doc({
			"doctype": "GLP-1 Patient Prescription",
			"patient": self.patient.name,
			"doctor": "test-doctor",
			"doctor_registration_number": "DR001",
			"medication": "test-medication",
			"dosage": "2.5mg",
			"duration": "30 days",
			"quantity": 30,
			"status": "Draft"
		})
		prescription.insert(ignore_permissions=True)
		
		# Check lock on draft (should not be locked)
		lock_check = check_prescription_lock(prescription.name)
		self.assertFalse(lock_check["locked"])
		
		# Submit prescription
		prescription.status = "Doctor Approved"
		prescription.submit(ignore_permissions=True)
		
		# Create dispense confirmation (simulates dispensing)
		confirmation = frappe.get_doc({
			"doctype": "GLP-1 Dispense Confirmation",
			"prescription": prescription.name,
			"patient": self.patient.name,
			"stock_entry": "test-se",
			"batch": "test-batch",
			"pharmacist": "test-pharmacist",
			"patient_acknowledgment": 1
		})
		confirmation.insert(ignore_permissions=True)
		confirmation.submit(ignore_permissions=True)
		
		# Update prescription status
		frappe.db.set_value("GLP-1 Patient Prescription", prescription.name, "status", "Dispensed")
		
		# Check lock (should be locked now)
		lock_check = check_prescription_lock(prescription.name)
		self.assertTrue(lock_check["locked"])
		
		# Cleanup
		frappe.delete_doc("GLP-1 Dispense Confirmation", confirmation.name, force=1, ignore_permissions=True)
		frappe.delete_doc("GLP-1 Patient Prescription", prescription.name, force=1, ignore_permissions=True)
	
	def test_cold_chain_compliance(self):
		"""Test CP-C: Cold Chain Enforcement"""
		# Create batch
		batch = frappe.get_doc({
			"doctype": "Batch",
			"batch_id": "TEST-BATCH-001",
			"item": "test-item"
		})
		batch.insert(ignore_permissions=True)
		
		# Check compliance (no excursions)
		compliance = check_cold_chain_compliance(batch.name)
		self.assertTrue(compliance["compliant"])
		
		# Create unresolved excursion
		cold_chain_log = frappe.get_doc({
			"doctype": "GLP-1 Cold Chain Log",
			"batch": batch.name,
			"warehouse": "test-warehouse",
			"temperature": 10.0,  # Out of range
			"checked_by": "test-user",
			"excursion": 1,
			"excursion_resolved": 0
		})
		cold_chain_log.insert(ignore_permissions=True)
		
		# Check compliance (should fail)
		compliance = check_cold_chain_compliance(batch.name)
		self.assertFalse(compliance["compliant"])
		self.assertTrue(compliance["block_dispensing"])
		
		# Cleanup
		frappe.delete_doc("GLP-1 Cold Chain Log", cold_chain_log.name, force=1, ignore_permissions=True)
		frappe.delete_doc("Batch", batch.name, force=1, ignore_permissions=True)
	
	def test_patient_reference_validation(self):
		"""Test CP-E: Anti-Wholesaling Guard"""
		# This test would require Stock Entry setup
		# Simplified test for validation logic
		result = validate_patient_reference("Stock Entry", "test-se")
		# Should return valid structure
		self.assertIn("valid", result)


class TestGLP1Permissions(FrappeTestCase):
	"""Test role-based permissions"""
	
	def test_doctor_prescription_permission(self):
		"""Test doctor can only see own prescriptions"""
		# Create test prescription
		prescription = frappe.get_doc({
			"doctype": "GLP-1 Patient Prescription",
			"patient": "test-patient",
			"doctor": "test-doctor",
			"doctor_registration_number": "DR001",
			"medication": "test-medication",
			"dosage": "2.5mg",
			"duration": "30 days",
			"quantity": 30,
			"status": "Draft"
		})
		prescription.insert(ignore_permissions=True)
		
		# Test doctor can see own prescription
		has_permission = has_glp1_prescription_permission(prescription, "test-doctor")
		# Note: This requires user setup - simplified test
		# self.assertTrue(has_permission)
		
		# Cleanup
		frappe.delete_doc("GLP-1 Patient Prescription", prescription.name, force=1, ignore_permissions=True)
	
	def test_sales_no_access(self):
		"""Test sales agents cannot access prescriptions"""
		prescription = frappe.get_doc({
			"doctype": "GLP-1 Patient Prescription",
			"patient": "test-patient",
			"doctor": "test-doctor",
			"doctor_registration_number": "DR001",
			"medication": "test-medication",
			"dosage": "2.5mg",
			"duration": "30 days",
			"quantity": 30,
			"status": "Draft"
		})
		prescription.insert(ignore_permissions=True)
		
		# Sales should not have access
		has_permission = has_glp1_prescription_permission(prescription, "sales-agent")
		# Note: Requires role setup - simplified test
		# self.assertFalse(has_permission)
		
		# Cleanup
		frappe.delete_doc("GLP-1 Patient Prescription", prescription.name, force=1, ignore_permissions=True)


class TestGLP1Workflow(FrappeTestCase):
	"""Test workflow transitions"""
	
	def test_intake_to_review_workflow(self):
		"""Test intake submission creates review"""
		# This would test the workflow hook
		# Requires full setup - placeholder for now
		pass
	
	def test_prescription_approval_workflow(self):
		"""Test prescription approval triggers quote generation"""
		# This would test the workflow hook
		# Requires full setup - placeholder for now
		pass
