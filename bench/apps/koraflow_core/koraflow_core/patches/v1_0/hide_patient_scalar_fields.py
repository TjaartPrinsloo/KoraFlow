import frappe

def execute():
    # 1. Unhide the Tab itself (so the Child Table or other content remains visible)
    if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}):
        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": "glp1_intake_tab"}, "hidden", 0)

    # 2. List of all scalar fields and sections to Hide
    fields_to_hide = [
        # From add_patient_fields.py
        "section_glp1_vitals", "intake_height_cm", "intake_weight_kg", "bmi", "bmi_category", "weight_to_lose",
        "section_glp1_safety", "intake_last_dose_date", "planned_surgery",
        
        # From add_patient_questions.py
        "section_glp1_high_risk", "medullary_thyroid_carcinoma", "men2_syndrome", "pancreatitis_history", 
        "gallstones_history", "gallbladder_removal", "column_break_glp1_gastro", "gastroparesis", 
        "frequent_nausea", "early_fullness",

        "section_glp1_organ", "kidney_disease_history", "egfr", "creatinine", "column_break_glp1_renal",
        "diabetic_retinopathy", "last_dilated_eye_exam", "heart_attack_history", "stroke_history", "heart_failure_history",

        "section_glp1_meds", "taking_insulin", "taking_sulfonylureas", "insulin_sulfonylurea_dose", 
        "column_break_glp1_meds", "narrow_therapeutic_window_drugs",

        "section_glp1_history_full", "medications_used_ozempic", "medications_used_wegovy", "medications_used_mounjaro",
        "medications_used_zepbound", "highest_dose_reached", "last_dose_date", "column_break_glp1_side_effects",
        "side_effects_nausea", "side_effects_vomiting", "side_effects_diarrhea", "side_effects_constipation",
        "side_effects_reflux", "side_effects_severity",

        "section_glp1_psych", "scoff_question_1", "scoff_question_2", "scoff_question_3", "scoff_question_4",
        "scoff_question_5", "column_break_glp1_motiv", "motivation_health", "motivation_appearance", 
        "motivation_mobility", "goal_weight",

        "section_glp1_repro", "pregnant", "breastfeeding", "planning_to_conceive"
    ]

    for fieldname in fields_to_hide:
        if frappe.db.exists("Custom Field", {"dt": "Patient", "fieldname": fieldname}):
            frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": fieldname}, "hidden", 1)
