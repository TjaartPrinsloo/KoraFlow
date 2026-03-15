import frappe
def verify_print_query():
    patient_id = "Lettie" # Based on the screenshot URL
    submissions = frappe.get_list("GLP-1 Intake Submission", 
        filters={"patient": patient_id}, 
        fields=["name"], 
        order_by="creation desc", 
        limit=1)
    print(f"Submissions for {patient_id}:", submissions)
    
    # Check hooks again
    hooks = frappe.get_hooks("doctype_js")
    print("Patient JS Hooks:", hooks.get("Patient"))
