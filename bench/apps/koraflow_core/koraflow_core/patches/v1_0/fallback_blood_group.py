import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # 1. Hide the stubborn Standard 'blood_group' field
    make_property_setter("Patient", "blood_group", "hidden", 1, "Check")
    
    # 2. Create a Custom Blood Group field in the right place
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_blood_group"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_blood_group",
            "label": "Blood Group",
            "fieldtype": "Select",
            "options": "\nA+\nA-\nB+\nB-\nAB+\nAB-\nO+\nO-",
            "insert_after": "section_key_biometrics",
            "hidden": 0
        }).insert(ignore_permissions=True)
    else:
        # Update if exists
         frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "custom_blood_group"}, "insert_after", "section_key_biometrics")
         frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "custom_blood_group"}, "hidden", 0)

    # 3. Anchor the rest of the chain to this new field
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "intake_height_cm"}, "insert_after", "custom_blood_group")
    
    # 4. Data Migration: Copy existing blood_group values to custom_blood_group
    frappe.db.sql("""
        UPDATE `tabPatient`
        SET custom_blood_group = blood_group
        WHERE blood_group IS NOT NULL AND blood_group != ''
    """)

    frappe.clear_cache(doctype="Patient")
