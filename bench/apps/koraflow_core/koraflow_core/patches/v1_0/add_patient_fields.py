import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Patient": [
            {
                "fieldname": "glp1_intake_tab",
                "fieldtype": "Tab Break",
                "label": "GLP-1 Intake",
                "insert_after": "medical_history_tab"
            },
            {
                "fieldname": "section_glp1_vitals",
                "fieldtype": "Section Break",
                "label": "Vital Metrics",
                "insert_after": "glp1_intake_tab"
            },
            {
                "fieldname": "intake_height_cm",
                "fieldtype": "Int",
                "label": "Height (cm)",
                "description": "Use whole numbers only [cite: 41]",
                "insert_after": "section_glp1_vitals"
            },
            {
                "fieldname": "intake_weight_kg",
                "fieldtype": "Float",
                "label": "Weight (kg)",
                "insert_after": "intake_height_cm"
            },
            {
                "fieldname": "bmi",
                "fieldtype": "Float",
                "label": "Calculated BMI",
                "read_only": 1,
                "description": "Formula: weight / (height/100)^2 [cite: 42]",
                "insert_after": "intake_weight_kg"
            },
            {
                "fieldname": "bmi_category",
                "fieldtype": "Data",
                "label": "BMI Category",
                "read_only": 1,
                "insert_after": "bmi"
            },
            {
                "fieldname": "weight_to_lose",
                "fieldtype": "Float",
                "label": "Kg to reach BMI 25",
                "read_only": 1,
                "description": "Visible to S2W staff only [cite: 46, 49]",
                "insert_after": "bmi_category"
            },
            {
                "fieldname": "section_glp1_safety",
                "fieldtype": "Section Break",
                "label": "Safety & History",
                "insert_after": "weight_to_lose"
            },
            {
                "fieldname": "intake_last_dose_date",
                "fieldtype": "Date",
                "label": "Date of Last Dose",
                "description": "If >14 days, tolerance may have reset [cite: 159]",
                "insert_after": "section_glp1_safety"
            },
            {
                "fieldname": "planned_surgery",
                "fieldtype": "Select",
                "label": "Any operations planned in 6 weeks?",
                "options": "No\nYes",
                "description": "GLP-1s must be stopped 7 days before anesthesia",
                "insert_after": "intake_last_dose_date"
            }
        ]
    }
    create_custom_fields(custom_fields, update=True)
