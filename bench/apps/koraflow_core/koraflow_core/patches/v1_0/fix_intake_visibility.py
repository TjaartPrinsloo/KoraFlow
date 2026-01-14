import frappe

def execute():
    # 1. Create a NEW Visible Section Break explicitly for the forms
    # We insert it after the last hidden field 'planning_to_conceive'
    # This 'closes' the previous hidden section and starts a empty visible one.
    if not frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_forms_visible"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Patient",
            "fieldname": "section_glp1_forms_visible",
            "label": "Intake Forms & Summary",
            "fieldtype": "Section Break",
            "insert_after": "planning_to_conceive",
            "hidden": 0,
            "collapsible": 0
        }).insert(ignore_permissions=True)
    else:
        # If it exists (rerun), ensure it's visible and correctly placed
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_forms_visible"}, "hidden", 0)
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_forms_visible"}, "insert_after", "planning_to_conceive")

    # 2. Move the Table to be after this new visible section
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}, "insert_after", "section_glp1_forms_visible")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}, "hidden", 0)

    # 3. Move the Summary to be after the table
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}, "insert_after", "glp1_intake_forms")
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}, "hidden", 0)

    frappe.clear_cache(doctype="Patient")
