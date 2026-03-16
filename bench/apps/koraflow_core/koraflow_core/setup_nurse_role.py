import frappe

def setup_roles_and_permissions():
    frappe.flags.in_patch = True

    # 1. Create Role
    if not frappe.db.exists("Role", "Nurse"):
        role = frappe.get_doc({
            "doctype": "Role",
            "role_name": "Nurse",
            "desk_access": 1
        })
        role.insert(ignore_permissions=True)
        print("Created Nurse Role")

    # 2. Create Role Profile
    if not frappe.db.exists("Role Profile", "Nurse Profile"):
        profile = frappe.get_doc({
            "doctype": "Role Profile",
            "role_profile": "Nurse Profile",
            "roles": [{"role": "Nurse"}]
        })
        # Bypass queue_action to avoid locking errors during script setup
        profile.queue_action = lambda *args, **kwargs: None
        profile.insert(ignore_permissions=True)
        print("Created Nurse Profile")

    # Set allowed modules for the profile if supported (Frappe doesn't natively map modules on Role Profile alone without User/Role mappings, but we'll do this on User creation).

    # 3. Configure DocType Permissions for Nurse role
    # IMPORTANT: Custom DocPerm overrides ALL standard DocPerm for a doctype.
    # We must only add Nurse-specific entries and NOT clear other roles' perms.
    nurse_doctypes = ["Patient", "Patient Appointment", "Patient Encounter", "Vital Signs", "Employee"]

    # Only clear Nurse-specific Custom DocPerms (not other roles)
    for dt in nurse_doctypes:
        frappe.db.delete("Custom DocPerm", {"parent": dt, "role": "Nurse"})
        print(f"Cleared Nurse Custom DocPerms for {dt}")

    # Patient: Nurse gets Read only
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Patient",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 0,
        "create": 0,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)

    # Patient Appointment: Nurse gets Read, Write, Create
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Patient Appointment",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)

    # Patient Encounter: Nurse gets Read, Write, Create (no submit — enforced server-side via block_nurse_submit)
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Patient Encounter",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)

    # Vital Signs: Nurse gets Read, Write, Create
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Vital Signs",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)

    # Employee: Nurse gets Read own
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Employee",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 0,
        "create": 0,
        "delete": 0,
        "submit": 0,
        "if_owner": 1
    }).insert(ignore_permissions=True)

    # Read-only access to linked doctypes needed for Patient Encounter forms
    read_only_doctypes = [
        "Medication", "Prescription Dosage", "Prescription Duration",
        "Healthcare Practitioner", "Healthcare Service Unit",
        "Complaint", "Diagnosis", "Appointment Type"
    ]
    for dt in read_only_doctypes:
        frappe.db.delete("Custom DocPerm", {"parent": dt, "role": "Nurse"})
        frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": dt,
            "role": "Nurse",
            "permlevel": 0,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0
        }).insert(ignore_permissions=True)
    print("Set read-only perms for linked healthcare doctypes")

    print("Set Nurse Custom DocPerms")

    # 4. Hide Modules (Block other apps via Role Profile or User Defaults)
    # We will enforce module blocking via the User hook.

    # 5. Add Issue (Support Ticket) permissions for Nurse
    frappe.db.delete("Custom DocPerm", {"parent": "Issue", "role": "Nurse"})
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "Issue",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 0,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)
    print("Set Issue Custom DocPerm for Nurse")

    # 6. Add GLP-1 Intake Review permissions for Nurse
    frappe.db.delete("Custom DocPerm", {"parent": "GLP-1 Intake Review", "role": "Nurse"})
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": "GLP-1 Intake Review",
        "role": "Nurse",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0
    }).insert(ignore_permissions=True)
    print("Set GLP-1 Intake Review Custom DocPerm for Nurse")

    # 7. Create Number Cards for Nurse Dashboard
    import json

    # Number Card labels — Frappe autonames using the label field
    card_definitions = [
        {
            "label": "Nurse Active Patients",
            "type": "Document Type",
            "document_type": "Patient",
            "function": "Count",
            "filters_json": json.dumps([["Patient", "status", "=", "Active"]]),
            "color": "#5e64ff",
            "is_public": 1,
            "is_standard": 1,
            "module": "KoraFlow Core",
            "show_percentage_stats": 0,
        },
        {
            "label": "Nurse Clinical Review Pending",
            "type": "Document Type",
            "document_type": "GLP-1 Intake Review",
            "function": "Count",
            "filters_json": json.dumps([["GLP-1 Intake Review", "status", "=", "Pending"]]),
            "color": "#ff9800",
            "is_public": 1,
            "is_standard": 1,
            "module": "KoraFlow Core",
            "show_percentage_stats": 0,
        },
        {
            "label": "Nurse Doctor Review Pending",
            "type": "Document Type",
            "document_type": "Patient Encounter",
            "function": "Count",
            "filters_json": json.dumps([["Patient Encounter", "docstatus", "=", "0"]]),
            "color": "#e53935",
            "is_public": 1,
            "is_standard": 1,
            "module": "KoraFlow Core",
            "show_percentage_stats": 0,
        },
        {
            "label": "Nurse Support Tickets",
            "type": "Custom",
            "document_type": "Issue",
            "method": "koraflow_core.workspace.nurse_view.number_cards.get_nurse_support_tickets",
            "color": "#9c27b0",
            "is_public": 1,
            "is_standard": 1,
            "module": "KoraFlow Core",
            "show_percentage_stats": 0,
        },
    ]

    # Clean up old cards
    for old_name in ["Nurse - Active Patients", "Nurse - Clinical Review Pending",
                     "Nurse - Doctor Review Pending", "Nurse - Patient Support Tickets",
                     "Active Patients", "Awaiting Clinical Review",
                     "Awaiting Doctor Review", "Open Support Tickets",
                     "Active Patients-1", "Awaiting Clinical Review-1",
                     "Awaiting Doctor Review-1", "Open Support Tickets-1"]:
        if frappe.db.exists("Number Card", old_name):
            frappe.delete_doc("Number Card", old_name, force=True)

    created_card_names = []
    for card_data in card_definitions:
        label = card_data["label"]
        # Delete if exists (Frappe autonames from label)
        if frappe.db.exists("Number Card", label):
            frappe.delete_doc("Number Card", label, force=True)
        card = frappe.get_doc({"doctype": "Number Card", **card_data})
        card.insert(ignore_permissions=True)
        created_card_names.append(card.name)
        print(f"Created Number Card: {card.name}")

    # Commit number cards so workspace can link to them
    frappe.db.commit()

    # 8. Create Nurse View Workspace with Number Cards + Shortcuts
    if frappe.db.exists("Workspace", "Nurse View"):
        frappe.delete_doc("Workspace", "Nurse View", force=True)
        print("Deleted old Nurse View Workspace")

    # Frontend matches number_card blocks by LABEL (not by name)
    card_labels = ["Active Patients", "Awaiting Clinical Review", "Awaiting Doctor Review", "Open Support Tickets"]

    content = json.dumps([
        # Header
        {"type": "header", "data": {"text": "<span class=\"h4\"><b>Nurse Dashboard</b></span>", "col": 12}},
        # 4 Number Cards in a row — use label values for frontend matching
        {"type": "number_card", "data": {"number_card_name": card_labels[0], "col": 3}},
        {"type": "number_card", "data": {"number_card_name": card_labels[1], "col": 3}},
        {"type": "number_card", "data": {"number_card_name": card_labels[2], "col": 3}},
        {"type": "number_card", "data": {"number_card_name": card_labels[3], "col": 3}},
        # Spacer
        {"type": "spacer", "data": {"col": 12}},
        # Quick Access header
        {"type": "header", "data": {"text": "<span class=\"h4\"><b>Quick Access</b></span>", "col": 12}},
        # 4 Shortcuts
        {"type": "shortcut", "data": {"shortcut_name": "Patient Appointment", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Patient", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Patient Encounter", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Vital Signs", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Support Tickets", "col": 3}},
    ])

    # Build number_cards child table from actual created names
    nc_child_table = []
    for i, card_name in enumerate(created_card_names):
        nc_child_table.append({"number_card_name": card_name, "label": card_labels[i]})

    ws = frappe.get_doc({
        "doctype": "Workspace",
        "name": "Nurse View",
        "label": "Nurse View",
        "title": "Nurse View",
        "module": "Healthcare",
        "public": 1,
        "roles": [{"role": "Nurse"}],
        "charts": [],
        "number_cards": nc_child_table,
        "shortcuts": [
            {
                "label": "Patient Appointment",
                "link_to": "Patient Appointment",
                "type": "DocType",
                "color": "Blue",
                "format": "{} Open",
                "stats_filter": '{"status":"Open"}'
            },
            {
                "label": "Patient",
                "link_to": "Patient",
                "type": "DocType",
                "color": "Grey"
            },
            {
                "label": "Patient Encounter",
                "link_to": "Patient Encounter",
                "type": "DocType",
                "color": "Orange",
                "format": "{} Draft",
                "stats_filter": '{"docstatus":0}'
            },
            {
                "label": "Vital Signs",
                "link_to": "Vital Signs",
                "type": "DocType",
                "color": "Green"
            },
            {
                "label": "Support Tickets",
                "link_to": "Issue",
                "type": "DocType",
                "color": "Purple",
                "format": "{} Open",
                "stats_filter": '{"status":"Open"}'
            },
        ],
        "content": content
    })
    ws.flags.ignore_links = True
    ws.insert(ignore_permissions=True)
    print("Created Nurse View Workspace with number cards and shortcuts")

    frappe.flags.in_patch = False
    frappe.db.commit()
    print("Nurse Role Setup Complete.")

if __name__ == "__main__":
    setup_roles_and_permissions()
