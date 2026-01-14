import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Patient": [
            # Section 2: High Release
            {
                "fieldname": "section_glp1_high_risk",
                "fieldtype": "Section Break",
                "label": "High-Risk Clinical Screening",
                "insert_after": "planned_surgery"
            },
            {
                "fieldname": "medullary_thyroid_carcinoma",
                "fieldtype": "Check",
                "label": "History of Medullary Thyroid Carcinoma (MTC)",
                "insert_after": "section_glp1_high_risk"
            },
            {
                "fieldname": "men2_syndrome",
                "fieldtype": "Check",
                "label": "History of Multiple Endocrine Neoplasia Type 2 (MEN 2)",
                "insert_after": "medullary_thyroid_carcinoma"
            },
            {
                "fieldname": "pancreatitis_history",
                "fieldtype": "Check",
                "label": "History of Pancreatitis",
                "insert_after": "men2_syndrome"
            },
            {
                "fieldname": "gallstones_history",
                "fieldtype": "Check",
                "label": "History of Gallstones",
                "insert_after": "pancreatitis_history"
            },
            {
                "fieldname": "gallbladder_removal",
                "fieldtype": "Check",
                "label": "Gallbladder Removal",
                "insert_after": "gallstones_history"
            },
            {
                "fieldname": "column_break_glp1_gastro",
                "fieldtype": "Column Break",
                "insert_after": "gallbladder_removal"
            },
            {
                "fieldname": "gastroparesis",
                "fieldtype": "Check",
                "label": "Diagnosed with Gastroparesis",
                "insert_after": "column_break_glp1_gastro"
            },
            {
                "fieldname": "frequent_nausea",
                "fieldtype": "Check",
                "label": "Frequent Nausea",
                "insert_after": "gastroparesis"
            },
            {
                "fieldname": "early_fullness",
                "fieldtype": "Check",
                "label": "Early Fullness",
                "insert_after": "frequent_nausea"
            },

            # Section 3: Organ Systems
            {
                "fieldname": "section_glp1_organ",
                "fieldtype": "Section Break",
                "label": "Organ Systems & Labs",
                "insert_after": "early_fullness"
            },
            {
                "fieldname": "kidney_disease_history",
                "fieldtype": "Check",
                "label": "History of Kidney Disease",
                "insert_after": "section_glp1_organ"
            },
            {
                "fieldname": "egfr",
                "fieldtype": "Float",
                "label": "eGFR (mL/min/1.73m²)",
                "insert_after": "kidney_disease_history"
            },
            {
                "fieldname": "creatinine",
                "fieldtype": "Float",
                "label": "Creatinine",
                "insert_after": "egfr"
            },
            {
                "fieldname": "column_break_glp1_renal",
                "fieldtype": "Column Break",
                "insert_after": "creatinine"
            },
            {
                "fieldname": "diabetic_retinopathy",
                "fieldtype": "Check",
                "label": "Diabetic Retinopathy (if Diabetic)",
                "insert_after": "column_break_glp1_renal"
            },
            {
                "fieldname": "last_dilated_eye_exam",
                "fieldtype": "Date",
                "label": "Date of Last Dilated Eye Exam",
                "insert_after": "diabetic_retinopathy"
            },
            {
                "fieldname": "heart_attack_history",
                "fieldtype": "Check",
                "label": "History of Heart Attack",
                "insert_after": "last_dilated_eye_exam"
            },
            {
                "fieldname": "stroke_history",
                "fieldtype": "Check",
                "label": "History of Stroke",
                "insert_after": "heart_attack_history"
            },
            {
                "fieldname": "heart_failure_history",
                "fieldtype": "Check",
                "label": "History of Heart Failure",
                "insert_after": "stroke_history"
            },

            # Section 4: Medication
            {
                "fieldname": "section_glp1_meds",
                "fieldtype": "Section Break",
                "label": "Current Medication",
                "insert_after": "heart_failure_history"
            },
            {
                "fieldname": "taking_insulin",
                "fieldtype": "Check",
                "label": "Taking Insulin",
                "insert_after": "section_glp1_meds"
            },
            {
                "fieldname": "taking_sulfonylureas",
                "fieldtype": "Check",
                "label": "Taking Sulfonylureas",
                "insert_after": "taking_insulin"
            },
            {
                "fieldname": "insulin_sulfonylurea_dose",
                "fieldtype": "Small Text",
                "label": "Current Dose (if Yes)",
                "insert_after": "taking_sulfonylureas"
            },
            {
                "fieldname": "column_break_glp1_meds",
                "fieldtype": "Column Break",
                "insert_after": "insulin_sulfonylurea_dose"
            },
            {
                "fieldname": "narrow_therapeutic_window_drugs",
                "fieldtype": "Small Text",
                "label": "Narrow Therapeutic Window Drugs",
                "insert_after": "column_break_glp1_meds"
            },

            # Section 5: GLP-1 History
            {
                "fieldname": "section_glp1_history_full",
                "fieldtype": "Section Break",
                "label": "GLP-1 History",
                "insert_after": "narrow_therapeutic_window_drugs"
            },
            {
                "fieldname": "medications_used_ozempic",
                "fieldtype": "Check",
                "label": "Ozempic",
                "insert_after": "section_glp1_history_full"
            },
            {
                "fieldname": "medications_used_wegovy",
                "fieldtype": "Check",
                "label": "Wegovy",
                "insert_after": "medications_used_ozempic"
            },
            {
                "fieldname": "medications_used_mounjaro",
                "fieldtype": "Check",
                "label": "Mounjaro",
                "insert_after": "medications_used_wegovy"
            },
            {
                "fieldname": "medications_used_zepbound",
                "fieldtype": "Check",
                "label": "Zepbound",
                "insert_after": "medications_used_mounjaro"
            },
            {
                "fieldname": "highest_dose_reached",
                "fieldtype": "Data",
                "label": "Highest Dose Reached",
                "insert_after": "medications_used_zepbound"
            },
            {
                "fieldname": "last_dose_date",
                "fieldtype": "Date",
                "label": "Date of Last Dose",
                "insert_after": "highest_dose_reached"
            },
            {
                "fieldname": "column_break_glp1_side_effects",
                "fieldtype": "Column Break",
                "insert_after": "last_dose_date"
            },
            {
                "fieldname": "side_effects_nausea",
                "fieldtype": "Check",
                "label": "Nausea",
                "insert_after": "column_break_glp1_side_effects"
            },
            {
                "fieldname": "side_effects_vomiting",
                "fieldtype": "Check",
                "label": "Vomiting",
                "insert_after": "side_effects_nausea"
            },
            {
                "fieldname": "side_effects_diarrhea",
                "fieldtype": "Check",
                "label": "Diarrhea",
                "insert_after": "side_effects_vomiting"
            },
            {
                "fieldname": "side_effects_constipation",
                "fieldtype": "Check",
                "label": "Constipation",
                "insert_after": "side_effects_diarrhea"
            },
            {
                "fieldname": "side_effects_reflux",
                "fieldtype": "Check",
                "label": "Reflux",
                "insert_after": "side_effects_constipation"
            },
            {
                "fieldname": "side_effects_severity",
                "fieldtype": "Int",
                "label": "Severity (1-10)",
                "insert_after": "side_effects_reflux"
            },

            # Section 6: Psychological
            {
                "fieldname": "section_glp1_psych",
                "fieldtype": "Section Break",
                "label": "Psychological Readiness (SCOFF)",
                "insert_after": "side_effects_severity"
            },
            {
                "fieldname": "scoff_question_1",
                "fieldtype": "Check",
                "label": "Sick because uncomfortably full?",
                "insert_after": "section_glp1_psych"
            },
            {
                "fieldname": "scoff_question_2",
                "fieldtype": "Check",
                "label": "Lost control over how much eat?",
                "insert_after": "scoff_question_1"
            },
            {
                "fieldname": "scoff_question_3",
                "fieldtype": "Check",
                "label": "Lost >14 lbs in 3 months?",
                "insert_after": "scoff_question_2"
            },
            {
                "fieldname": "scoff_question_4",
                "fieldtype": "Check",
                "label": "Believe fat when others say thin?",
                "insert_after": "scoff_question_3"
            },
            {
                "fieldname": "scoff_question_5",
                "fieldtype": "Check",
                "label": "Food dominates life?",
                "insert_after": "scoff_question_4"
            },
            {
                "fieldname": "column_break_glp1_motiv",
                "fieldtype": "Column Break",
                "insert_after": "scoff_question_5"
            },
            {
                "fieldname": "motivation_health",
                "fieldtype": "Check",
                "label": "Motivation: Health",
                "insert_after": "column_break_glp1_motiv"
            },
            {
                "fieldname": "motivation_appearance",
                "fieldtype": "Check",
                "label": "Motivation: Appearance",
                "insert_after": "motivation_health"
            },
            {
                "fieldname": "motivation_mobility",
                "fieldtype": "Check",
                "label": "Motivation: Mobility",
                "insert_after": "motivation_appearance"
            },
            {
                "fieldname": "goal_weight",
                "fieldtype": "Float",
                "label": "Goal Weight",
                "insert_after": "motivation_mobility"
            },

            # Section 7: Reproductive
            {
                "fieldname": "section_glp1_repro",
                "fieldtype": "Section Break",
                "label": "Reproductive Health",
                "insert_after": "goal_weight"
            },
            {
                "fieldname": "pregnant",
                "fieldtype": "Check",
                "label": "Pregnant?",
                "insert_after": "section_glp1_repro"
            },
            {
                "fieldname": "breastfeeding",
                "fieldtype": "Check",
                "label": "Breastfeeding?",
                "insert_after": "pregnant"
            },
            {
                "fieldname": "planning_to_conceive",
                "fieldtype": "Check",
                "label": "Planning to conceive?",
                "insert_after": "breastfeeding"
            }
        ]
    }
    create_custom_fields(custom_fields, update=True)
