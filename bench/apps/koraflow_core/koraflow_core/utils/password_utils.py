import re
import frappe
from frappe import _

def validate_password_strength(password):
    """
    Validates password strength based on the following policy:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if not password:
        frappe.throw(_("Password is required"), frappe.ValidationError)

    if len(password) < 8:
        frappe.throw(_("Password must be at least 8 characters long"), frappe.ValidationError)
        
    if not re.search(r"[A-Z]", password):
        frappe.throw(_("Password must contain at least one uppercase letter"), frappe.ValidationError)
        
    if not re.search(r"[a-z]", password):
        frappe.throw(_("Password must contain at least one lowercase letter"), frappe.ValidationError)
        
    if not re.search(r"\d", password):
        frappe.throw(_("Password must contain at least one number"), frappe.ValidationError)
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        frappe.throw(_("Password must contain at least one special character"), frappe.ValidationError)
        
    return True
