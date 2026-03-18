import frappe

def sync_address_and_contact(doc, method=None):
    """
    Sync Patient address and contact details to standard Address and Contact records.
    Triggered on Patient on_update.
    """
    if frappe.flags.in_patch or frappe.flags.in_install or frappe.flags.in_migrate:
        return

    sync_address(doc)
    sync_contact(doc)

def sync_address(doc):
    """Sync address from Patient custom fields to a linked Address document.
    Address data comes from the intake form and is stored via patient_sync._sync_patient_address.
    This hook only syncs if custom address fields have data (e.g. updated via patient portal)."""
    address_line1 = getattr(doc, 'custom_address_line1', None)
    city = getattr(doc, 'custom_city', None)

    if not address_line1 and not city:
        return

    address_line2 = getattr(doc, 'custom_address_line2', None)
    state = getattr(doc, 'custom_state', None)
    pincode = getattr(doc, 'custom_pincode', None)
    country = getattr(doc, 'custom_country', None) or "South Africa"

    # Check if a primary address already exists for this patient
    existing_addresses = frappe.get_all("Dynamic Link", filters={
        "link_doctype": "Patient",
        "link_name": doc.name,
        "parenttype": "Address"
    }, pluck="parent")

    if existing_addresses:
        address_doc = frappe.get_doc("Address", existing_addresses[0])
    else:
        address_doc = frappe.new_doc("Address")
        address_doc.address_title = doc.patient_name or doc.first_name
        address_doc.address_type = "Shipping"
        address_doc.append("links", {
            "link_doctype": "Patient",
            "link_name": doc.name
        })

    address_doc.update({
        "address_line1": address_line1,
        "address_line2": address_line2 if address_line2 != address_line1 else None,
        "city": city,
        "state": state,
        "pincode": pincode,
        "country": country,
        "email_id": doc.email,
        "phone": doc.mobile
    })

    address_doc.flags.ignore_permissions = True
    address_doc.save()

def sync_contact(doc):
    if not doc.email and not doc.mobile:
        return

    # Check if a contact already exists
    existing_contacts = frappe.get_all("Dynamic Link", filters={
        "link_doctype": "Patient",
        "link_name": doc.name,
        "parenttype": "Contact"
    }, pluck="parent")

    if existing_contacts:
        contact_doc = frappe.get_doc("Contact", existing_contacts[0])
    else:
        contact_doc = frappe.new_doc("Contact")
        contact_doc.first_name = doc.first_name
        contact_doc.last_name = doc.last_name
        contact_doc.append("links", {
            "link_doctype": "Patient",
            "link_name": doc.name
        })

    # Update email
    if doc.email:
        has_email = False
        for email in contact_doc.email_ids:
            if email.email_id == doc.email:
                has_email = True
                email.is_primary = 1
                break
        if not has_email:
            contact_doc.append("email_ids", {
                "email_id": doc.email,
                "is_primary": 1
            })

    # Update phone
    if doc.mobile:
        has_phone = False
        for phone in contact_doc.phone_nos:
            if phone.phone == doc.mobile:
                has_phone = True
                phone.is_primary_mobile_no = 1
                break
        if not has_phone:
            contact_doc.append("phone_nos", {
                "phone": doc.mobile,
                "is_primary_mobile_no": 1
            })

    contact_doc.flags.ignore_permissions = True
    contact_doc.save()

def migrate_all_patients():
    """Migrate all existing patients to Address and Contact."""
    patients = frappe.get_all("Patient")
    total = len(patients)
    print(f"Syncing {total} patients...")
    
    for i, p in enumerate(patients):
        try:
            doc = frappe.get_doc("Patient", p.name)
            sync_address_and_contact(doc)
            if i % 10 == 0:
                frappe.db.commit()
                print(f"Synced {i+1}/{total}...")
        except Exception as e:
            print(f"Error syncing patient {p.name}: {str(e)}")
    
    frappe.db.commit()
    print("Migration complete!")

def add_nurse_permissions():
    """Add Read and Write permissions for Nurse on Address and Contact."""
    from frappe.permissions import add_permission
    for doctype in ["Address", "Contact"]:
        try:
            add_permission(doctype, "Nurse", 0, "read")
            add_permission(doctype, "Nurse", 0, "write")
        except Exception as e:
            print(f"Permission already exists or error for {doctype}: {str(e)}")
    
    frappe.db.commit()
    print("Nurse permissions updated for Address and Contact.")
