import frappe

def execute():
    # Move the 'GLP-1 Intake Forms' table to be after the last field of our hidden sections
    # This ensures it sits at the bottom of the 'GLP-1 Intake' tab
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}, "insert_after", "planning_to_conceive")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}, "hidden", 0) # Ensure visible

    # Move 'AI Medical Summary' to be after the forms table
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}, "insert_after", "glp1_intake_forms")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}, "hidden", 0) # Ensure visible

    # Re-apply property setters just in case (optional, but safe)
    frappe.clear_cache(doctype="Patient")
