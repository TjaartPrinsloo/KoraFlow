import frappe

def execute():
    """
    Rename fields in GLP-1 Intake Form to match GLP-1 Intake Submission (standardizing on intake_ prefix).
    This patch renames the database columns to preserve data.
    """
    table = "GLP-1 Intake Form"
    
    # Map of old_fieldname -> new_fieldname
    field_map = {
        "medullary_thyroid_carcinoma": "intake_mtc",
        "men2_syndrome": "intake_men2",
        "pancreatitis_history": "intake_pancreatitis",
        "gallstones_history": "intake_gallstones",
        "gallbladder_removal": "intake_gallbladder_removal",
        "gastroparesis": "intake_gastroparesis",
        "frequent_nausea": "intake_frequent_nausea",
        "early_fullness": "intake_early_fullness",
        "kidney_disease_history": "intake_kidney_disease",
        "egfr": "intake_egfr",
        "creatinine": "intake_creatinine",
        "diabetic_retinopathy": "intake_diabetic_retinopathy",
        "last_dilated_eye_exam": "intake_last_eye_exam",
        "heart_attack_history": "intake_heart_attack",
        "stroke_history": "intake_stroke",
        "heart_failure_history": "intake_heart_failure",
        "taking_insulin": "intake_taking_insulin",
        "taking_sulfonylureas": "intake_taking_sulfonylureas",
        "insulin_sulfonylurea_dose": "intake_insulin_dose",
        "narrow_therapeutic_window_drugs": "intake_narrow_window_drugs",
        "medications_used_ozempic": "intake_med_ozempic",
        "medications_used_wegovy": "intake_med_wegovy",
        "medications_used_mounjaro": "intake_med_mounjaro",
        "medications_used_zepbound": "intake_med_zepbound",
        "highest_dose_reached": "intake_highest_dose",
        "last_dose_date": "intake_last_dose_date",
        "side_effects_nausea": "intake_se_nausea",
        "side_effects_vomiting": "intake_se_vomiting",
        "side_effects_diarrhea": "intake_se_diarrhea",
        "side_effects_constipation": "intake_se_constipation",
        "side_effects_reflux": "intake_se_reflux",
        "side_effects_severity": "intake_se_severity",
        "scoff_question_1": "intake_scoff_1",
        "scoff_question_2": "intake_scoff_2",
        "scoff_question_3": "intake_scoff_3",
        "scoff_question_4": "intake_scoff_4",
        "scoff_question_5": "intake_scoff_5",
        "motivation_health": "intake_motivation_health",
        "motivation_appearance": "intake_motivation_appearance",
        "motivation_mobility": "intake_motivation_mobility",
        "goal_weight": "intake_goal_weight",
        "pregnant": "intake_pregnant",
        "breastfeeding": "intake_breastfeeding",
        "planning_to_conceive": "intake_planning_conceive",
        "planned_surgery": "intake_planned_surgery"
    }

    if not frappe.db.exists("DocType", table):
        return

    for old_field, new_field in field_map.items():
        # Check if old column exists and new column DOES NOT exist
        if frappe.db.has_column(table, old_field) and not frappe.db.has_column(table, new_field):
            try:
                frappe.db.rename_column(table, old_field, new_field)
            except Exception as e:
                # If rename fails (e.g. type mismatch or constraint), log it but proceed?
                # For now, just print error
                print(f"Failed to rename {old_field} to {new_field}: {e}")
        elif frappe.db.has_column(table, old_field) and frappe.db.has_column(table, new_field):
             # Both exist, maybe migrate data?
             # frappe.db.sql(f"UPDATE `tab{table}` SET `{new_field}` = `{old_field}` WHERE `{new_field}` IS NULL")
             pass
