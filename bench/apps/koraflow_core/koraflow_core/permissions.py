import frappe
from frappe import _

def get_nurse_appointment_conditions(user):
    # Nurses can see all appointments now 
    return ""


def get_nurse_patient_conditions(user):
    # Nurses can see all patients now, no appointment filtering required
    return ""

def patient_has_permission(doc, ptype, user):
    if "Nurse" not in frappe.get_roles(user):
        return True  # Let other roles handle it normally
    
    # Nurses can READ and WRITE patient (UI handles field-level visibility)
    if ptype in ("read", "select", "write"):
        return True
    
    return False

def block_nurse_submit(doc, method):
    """Hard server-side block — nurses cannot submit encounters under any circumstance."""
    if "Nurse" in frappe.get_roles(frappe.session.user):
        frappe.throw(
            _("Nurses can only save Patient Encounters as Draft. Only a Doctor can submit an encounter."),
            frappe.PermissionError
        )

def after_insert_user(doc, method):
    print(f"Hook triggered for {doc.name}, method {method}, flag: {getattr(doc.flags, 'in_nurse_update', False)}")
    if doc.flags.in_nurse_update or doc.doctype != "User":
        return
        
    roles = [r.role for r in doc.get("roles", [])]
    print(f"Roles for {doc.name}: {roles}")
    if "Nurse" in roles:

        # Get all available modules
        all_modules = [m.name for m in frappe.get_all("Module Def")]
        
        # Modules that MUST be allowed (NOT in block list)
        allowed_modules = ["Healthcare"]
        
        # Everything else should be blocked
        expected_blocks = [m for m in all_modules if m not in allowed_modules]
        
        # Get current blocks
        current_blocks = [m.module for m in doc.get("block_modules", [])]
        
        # Check if we need to update (using sets for accurate comparison)
        if set(expected_blocks) != set(current_blocks):
            doc.set("block_modules", [{"module": m} for m in expected_blocks])
            doc.flags.in_nurse_update = True
            doc.flags.ignore_permissions = True
            doc.save()

