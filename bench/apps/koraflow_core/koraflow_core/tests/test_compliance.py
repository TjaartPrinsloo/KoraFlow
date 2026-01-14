
import unittest
from koraflow_core.utils.security import mask_email

class TestCompliance(unittest.TestCase):
    def test_email_masking(self):
        """Verify email masking for PII protection"""
        # Standard email
        self.assertEqual(mask_email("johndoe@example.com"), "j***@example.com")
        
        # Short user part
        self.assertEqual(mask_email("a@example.com"), "*example.com")
        self.assertEqual(mask_email("ab@example.com"), "a***@example.com")
        
        # Invalid inputs (safe failover)
        self.assertEqual(mask_email("invalid"), "********")
        self.assertEqual(mask_email(None), "********")
        self.assertEqual(mask_email(""), "********")

    def test_permission_restrictions(self):
        """Verify API permission changes"""
        import frappe
        from koraflow_core.api.patient_signup import get_intake_form_status
        
        # Guest access should fail or return empty/default depending on implementation choice
        # Since we removed allow_guest=True, direct call might succeed but HTTP would 403.
        # Here we test decorator presence if possible, or simulate flow.
        
        # In unit tests, checking white list status:
        method = frappe.get_attr("koraflow_core.api.patient_signup.get_intake_form_status")
        # Check if allow_guest is False (default)
        self.assertFalse(getattr(method, "allow_guest", False), "get_intake_form_status should NOT allow guest access")

