import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # We want the 'Personal and Social History' section to appear right after 'patient_details'
    # AND before 'dashboard_tab'.
    # Currently, 'dashboard_tab' follows 'patient_details' immediately in standard order.
    # Inserting 'personal_and_social_history' after 'patient_details' resulted in a conflict/race where Dashboard still came first.
    
    # SOLUTION:
    # 1. Ensure 'personal_and_social_history' is after 'patient_details' (Already done, but enforcing)
    make_property_setter("Patient", "personal_and_social_history", "insert_after", "patient_details", "Section Break")
    
    # 2. Push 'dashboard_tab' to be AFTER the last field of 'Personal and Social History' section
    # The section ends with 'marital_status'.
    make_property_setter("Patient", "dashboard_tab", "insert_after", "marital_status", "Tab Break")

    # 3. Ensure intermediate fields are chained correctly just in case
    # occupation links to personal_and_social_history
    # marital_status links to column_break_25 (which links to occupation)
    # This chain seems fine from previous debug output.

    frappe.clear_cache(doctype="Patient")
