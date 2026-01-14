import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # Strategy: Duplicate Fields for Personal History because standard fields refuse to move.
    # New fields will be inserted after 'custom_personal_history' (which is reliably at position 30).
    
    # 1. Hide Standard Fields
    fields_to_hide = ["occupation", "column_break_25", "marital_status"]
    for f in fields_to_hide:
        make_property_setter("Patient", f, "hidden", 1, "Data" if f=="occupation" else ("Select" if f=="marital_status" else "Column Break"))
        
    # 2. Create Custom Duplicates
    
    # Occupation
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_occupation"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_occupation",
            "label": "Occupation",
            "fieldtype": "Data",
            "insert_after": "custom_personal_history",
            "hidden": 0
        }).insert(ignore_permissions=True)
        
    # Column Break
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_cb_history"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_cb_history",
            "fieldtype": "Column Break",
            "insert_after": "custom_occupation",
            "hidden": 0
        }).insert(ignore_permissions=True)
        
    # Marital Status
    # Fetch options from standard field
    ms_meta = frappe.get_meta("Patient").get_field("marital_status")
    options = ms_meta.options or "\nSingle\nMarried\nDivorced\nWidowed"
    
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "custom_marital_status"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "custom_marital_status",
            "label": "Marital Status",
            "fieldtype": "Select",
            "options": options,
            "insert_after": "custom_cb_history",
            "hidden": 0
        }).insert(ignore_permissions=True)
        
    # 3. Migrate Data
    frappe.db.sql("""
        UPDATE `tabPatient`
        SET custom_occupation = occupation
        WHERE occupation IS NOT NULL AND occupation != ''
    """)
    frappe.db.sql("""
        UPDATE `tabPatient`
        SET custom_marital_status = marital_status
        WHERE marital_status IS NOT NULL AND marital_status != ''
    """)

    frappe.clear_cache(doctype="Patient")
