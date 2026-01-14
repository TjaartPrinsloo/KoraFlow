import frappe

def execute():
    fields = ["glp1_intake_tab", "intake_height_cm", "section_glp1_high_risk"]
    results = {}
    for f in fields:
        val = frappe.db.get_value("Custom Field", {"dt": "Patient", "fieldname": f}, "hidden")
        results[f] = val
    print(f"DEBUG_RESULTS: {results}")

    # FORCE UPDATE if not hidden
    # Uncomment to force fix in this script if needed
    # for f in fields:
    #     if f != "glp1_intake_tab": # Keep tab visible
    #        frappe.db.set_value("Custom Field", {"dt": "Patient", "fieldname": f}, "hidden", 1)
    # frappe.db.commit()
