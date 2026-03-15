import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def add_field():
    print("Adding custom_allow_intake_retake field to Patient...")
    
    custom_fields = {
        "Patient": [
            {
                "fieldname": "custom_allow_intake_retake",
                "label": "Allow Intake Retake",
                "fieldtype": "Check",
                "insert_after": "mobile", # Adjust position as needed
                "default": 0,
                "description": "If checked, the patient can retake the GLP-1 intake form even if one exists."
            }
        ]
    }
    
    create_custom_fields(custom_fields)
    print("Field added successfully.")
    
add_field()
