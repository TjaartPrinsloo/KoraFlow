import frappe

@frappe.whitelist()
def get_nurse_support_tickets():
    """Count open Issues for patients assigned to the current nurse."""
    user = frappe.session.user

    # Get patients assigned to this nurse
    patients = frappe.get_all(
        "Patient",
        filters={"custom_assigned_nurse": user},
        pluck="name",
        ignore_permissions=True
    )

    if not patients:
        return {
            "value": 0,
            "fieldtype": "Int",
            "route": "/app/issue",
            "route_options": {"status": "Open"}
        }

    count = frappe.db.count("Issue", {
        "custom_patient": ["in", patients],
        "status": "Open"
    })

    return {
        "value": count,
        "fieldtype": "Int",
        "route": "/app/issue",
        "route_options": {"status": "Open"}
    }
