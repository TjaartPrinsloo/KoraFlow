import frappe
from frappe.utils import add_user_credential

def setup_roles():
    """
    Ensure standard roles exist and have correct permissions.
    """
    ROLES = [
        "Medical Practitioner",
        "Clinical Reviewer", 
        "Operations Staff",
        "Auditor",
        "Support"
    ]

    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
                "read_only": 1 if role in ["Auditor", "Support"] else 0
            }).insert()
            print(f"Created Role: {role}")

    # Set Permissions (Example: Auditor Read-Only on Patient)
    set_permission("Patient", "Auditor", 0) # Level 0
    set_permission("Patient Encounter", "Auditor", 0)

    # Medical Practitioner - Read/Write Own
    set_permission("Patient Encounter", "Medical Practitioner", 0, write=1, create=1)

def set_permission(doctype, role, level, read=1, write=0, create=0, delete=0, amend=0, report=0, export=0, share=0):
    if not frappe.db.exists("DocType", doctype):
        return

    # Check if permission exists
    perm_name = frappe.db.get_value("Custom DocPerm", {
        "parent": doctype,
        "role": role,
        "permlevel": level,
        "if_owner": 0
    })

    if not perm_name:
        # We generally use Custom DocPerm for site-specific overrides
        # But for an app, we should modify the DocType JSON. 
        # However, to enforce it without touching JSONs now:
        d = frappe.new_doc("Custom DocPerm")
        d.parent = doctype
        d.role = role
        d.permlevel = level
        d.read = read
        d.write = write
        d.create = create
        d.delete = delete
        d.amend = amend
        d.report = report
        d.export = export
        d.share = share
        d.insert(ignore_permissions=True)
        print(f"Set Custom permission for {role} on {doctype}")

