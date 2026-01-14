import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # 1. VISIBLE: Key Biometrics Section
    # Insert at top of GLP-1 Intake Tab
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "insert_after", "glp1_intake_tab")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_key_biometrics"}, "hidden", 0)

    # 2. VISIBLE: Blood Group (Standard Field -> Move via Property Setter)
    make_property_setter("Patient", "blood_group", "insert_after", "section_key_biometrics", "Data")
    
    # 3. VISIBLE: Key Biometric Fields
    # Sequence: Blood Group -> Height -> Weight -> BMI -> BMI Cat -> Goal -> To Lose
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "intake_height_cm"}, "insert_after", "blood_group")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "intake_weight_kg"}, "insert_after", "intake_height_cm")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "bmi"}, "insert_after", "intake_weight_kg")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "bmi_category"}, "insert_after", "bmi")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "goal_weight"}, "insert_after", "bmi_category")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "weight_to_lose"}, "insert_after", "goal_weight")

    # 4. VISIBLE: Intake Forms & Summary Section
    # Insert after the last biometric field
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_forms_visible"}, "insert_after", "weight_to_lose")
    
    # Ensure Forms and Summary are inside this section
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_forms"}, "insert_after", "section_glp1_forms_visible")
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "ai_medical_summary"}, "insert_after", "glp1_intake_forms")

    # 5. HIDDEN: Original Scalar Sections
    # Push the start of the hidden stack ('section_glp1_vitals') to be AFTER the visible stuff
    # This prevents the visible stuff from being swallowed if they were accidentally placed after a hidden section
    frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "section_glp1_vitals"}, "insert_after", "ai_medical_summary")

    frappe.clear_cache(doctype="Patient")
