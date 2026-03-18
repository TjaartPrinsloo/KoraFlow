from frappe import _

def get_data(data=None):
    # Try to get the original patient dashboard data from healthcare app
    try:
        from healthcare.healthcare.doctype.patient.patient_dashboard import get_data as get_original_data
        original_data = get_original_data()
        if original_data and isinstance(original_data, dict):
            if not data:
                data = original_data
            else:
                for k, v in original_data.items():
                    if isinstance(v, list) and k in data:
                        data[k].extend(v)
                    elif k not in data:
                        data[k] = v
    except ImportError:
        pass

    if not data:
        data = {}

    if "transactions" not in data:
        data["transactions"] = []
    
    # Check if GLP-1 Intake is already in transactions
    glp1_group = None
    for group in data["transactions"]:
        if group.get("label") == _("GLP-1 Intake"):
            glp1_group = group
            break
            
    if not glp1_group:
        glp1_group = {
            "label": _("GLP-1 Intake"),
            "items": []
        }
        data["transactions"].append(glp1_group)
        
    # Only show GLP-1 Intake Submission (the active doctype)
    if "GLP-1 Intake Submission" not in glp1_group["items"]:
        glp1_group["items"].append("GLP-1 Intake Submission")

    # Remove old GLP-1 Intake Form if present
    if "GLP-1 Intake Form" in glp1_group["items"]:
        glp1_group["items"].remove("GLP-1 Intake Form")

    if "non_standard_fieldnames" not in data:
        data["non_standard_fieldnames"] = {}

    data["non_standard_fieldnames"]["GLP-1 Intake Submission"] = "patient"

    return data
