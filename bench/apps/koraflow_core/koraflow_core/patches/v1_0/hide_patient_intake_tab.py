import frappe

def execute():
    # Set the 'hidden' property to 1 for the 'glp1_intake_tab' Custom Field on Patient
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}, "hidden", 1)
        # Also hide the high risk section just in case, though tab hiding should cover it
        # frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_high_risk"}, "hidden", 1)
