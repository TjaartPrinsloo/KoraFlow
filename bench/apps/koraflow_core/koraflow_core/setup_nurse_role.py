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

    # 3. Configure DocType Permissions
    doctypes_to_reset = ["Patient", "Patient Encounter", "Vital Signs", "Employee"]
    
    # Let's ensure Nurse doesn't have existing perms that are wrong
    for dt in doctypes_to_reset:
        frappe.db.delete("Custom DocPerm", {"parent": dt, "role": "Nurse"})
        print(f"Cleared existing Custom DocPerms for {dt}")

    # Patient: Read only
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

    # Patient Encounter: Read, Write, Create
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

    # Vital Signs: Read, Write, Create
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

    # Employee: Read own (if user linked to employee)
    # The actual standard rule for `Employee` is usually already `read` if `if_owner` but let's be explicit
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
    
    print("Set Custom DocPerms")

    # 4. Hide Modules (Block other apps via Role Profile or User Defaults)
    # We will enforce module blocking via the User hook.
    
    # 5. Create Nurse Workspace (if not exists)
    if not frappe.db.exists("Workspace", "Nurse View"):
        ws = frappe.get_doc({
            "doctype": "Workspace",
            "name": "Nurse View",
            "label": "Nurse View",
            "title": "Nurse View",
            "module": "Healthcare",
            "roles": [{"role": "Nurse"}],
            "charts": [],
            "shortcuts": [
                {
                    "label": "Waiting Patients",
                    "link_to": "Patient Appointment",
                    "type": "DocType",
                    "format": "List",
                    "stats_filter": '[["status","=","Open"]]',
                    "color": "Grey"
                }
            ],
            "content": '[{"id":"shortcuts","type":"shortcut","data":{"shortcut_name":"Waiting Patients"}}]'
        })
        ws.insert(ignore_permissions=True)
        print("Created Nurse View Workspace")
    else:
        # Update roles of existing WS if needed
        ws = frappe.get_doc("Workspace", "Nurse View")
        has_nurse = False
        for r in ws.roles:
            if r.role == "Nurse":
                has_nurse = True
        if not has_nurse:
            ws.append("roles", {"role": "Nurse"})
            ws.save(ignore_permissions=True)

    frappe.flags.in_patch = False
    frappe.db.commit()
    print("Nurse Role Setup Complete.")

if __name__ == "__main__":
    setup_roles_and_permissions()
