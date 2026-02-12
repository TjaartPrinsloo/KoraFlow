"""Helper to add missing custom field"""
import frappe

def add_referrer_field():
    # Check if field exists
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_referrer_name"}):
        doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_referrer_name",
            "label": "Referrer Name",
            "fieldtype": "Data",
            "insert_after": "patient_name",
            "read_only": 0
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("✅ Added custom_referrer_name to Patient")
    else:
        print("✅ Field already exists")
    
    # Verify
    meta = frappe.get_meta("Patient")
    fields = [f.fieldname for f in meta.fields]
    if "custom_referrer_name" in fields:
        print("✅ Verified: Field is now in Patient meta")
    else:
        print("❌ Field not found in meta - may need clear-cache")
