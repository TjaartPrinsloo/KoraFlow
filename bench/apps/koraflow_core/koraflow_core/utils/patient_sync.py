import frappe
from frappe import _

def sync_intake_to_patient(doc, method):
    """
    Syncs data from the latest GLP-1 Intake Form (child table) to the Patient parent fields.
    Hooked to Patient.before_save
    """
    if not doc.get("glp1_intake_forms"):
        # frappe.msgprint("Debug: No intake forms found on Patient.")
        return

    # Get the latest intake form (last in the list)
    latest_intake = doc.glp1_intake_forms[-1]
    
    # frappe.msgprint(f"Debug: Found intake form {latest_intake.name}. UID: {latest_intake.get('sa_id_number')}, Wt: {latest_intake.get('intake_weight_kg')}")
    
    # 1. Sync ID Number (UID) and Custom ID Field
    # Intake field: sa_id_number
    # Patient field (legacy): uid
    # Patient field (custom): custom_sa_id_number
    
    sa_id = latest_intake.get("sa_id_number")
    passport = latest_intake.get("passport_number")
    
    # Sync UID (best available ID)
    new_uid = (sa_id or passport or latest_intake.get("id_number"))
    if new_uid:
        if not doc.uid or doc.uid != new_uid:
            frappe.db.set_value("Patient", doc.name, "uid", new_uid)

    # Sync specific SA ID field
    if sa_id:
         # Check if field exists ("custom_sa_id_number" per patch)
         if hasattr(doc, "custom_sa_id_number") or "custom_sa_id_number" in doc.as_dict():
             frappe.db.set_value("Patient", doc.name, "custom_sa_id_number", sa_id)
         # Also try "sa_id_number" if custom field naming was different
         elif hasattr(doc, "sa_id_number") or "sa_id_number" in doc.as_dict():
             frappe.db.set_value("Patient", doc.name, "sa_id_number", sa_id)

    # 2. Sync Personal Details (DOB, Sex, Blood Group, Mobile, Last Name)
    if latest_intake.get("dob"):
        frappe.db.set_value("Patient", doc.name, "dob", latest_intake.get("dob"))
        
    if latest_intake.get("sex"):
        frappe.db.set_value("Patient", doc.name, "sex", latest_intake.get("sex"))

    if latest_intake.get("blood_group"):
        bg = latest_intake.get("blood_group")
        # Map short codes to Patient DocType strict options
        bg_map = {
            "A+": "A Positive", "A-": "A Negative",
            "B+": "B Positive", "B-": "B Negative",
            "AB+": "AB Positive", "AB-": "AB Negative",
            "O+": "O Positive", "O-": "O Negative"
        }
        final_bg = bg_map.get(bg, bg) # Fallback to original if already correct or unknown
        
        if hasattr(doc, "blood_group") or "blood_group" in doc.as_dict():
            frappe.db.set_value("Patient", doc.name, "blood_group", final_bg)
            
    if latest_intake.get("mobile"):
        frappe.db.set_value("Patient", doc.name, "mobile", latest_intake.get("mobile"))
        
    if latest_intake.get("last_name"):
        frappe.db.set_value("Patient", doc.name, "last_name", latest_intake.get("last_name"))

    # 3. Sync Vitals (Weight, Height, BMI, Goal Weight)
    # Fields on Patient created by add_patient_fields.py are:
    # intake_weight_kg, intake_height_cm, bmi
    
    # Weight
    if latest_intake.get("intake_weight_kg"):
         frappe.db.set_value("Patient", doc.name, "intake_weight_kg", latest_intake.get("intake_weight_kg"))
             
    # Height
    if latest_intake.get("intake_height_cm"):
         frappe.db.set_value("Patient", doc.name, "intake_height_cm", latest_intake.get("intake_height_cm"))

    # Goal Weight
    if latest_intake.get("intake_goal_weight"):
        # Fieldname guess: intake_goal_weight or goal_weight
        if hasattr(doc, "intake_goal_weight") or "intake_goal_weight" in doc.as_dict():
            frappe.db.set_value("Patient", doc.name, "intake_goal_weight", latest_intake.get("intake_goal_weight"))
        elif hasattr(doc, "goal_weight") or "goal_weight" in doc.as_dict():
            frappe.db.set_value("Patient", doc.name, "goal_weight", latest_intake.get("intake_goal_weight"))

    # BMI
    if latest_intake.get("intake_weight_kg") and latest_intake.get("intake_height_cm"):
        try:
            wt = float(latest_intake.get("intake_weight_kg"))
            ht = float(latest_intake.get("intake_height_cm"))
            if ht > 0:
                bmi = wt / ((ht/100) ** 2)
                frappe.db.set_value("Patient", doc.name, "bmi", round(bmi, 1))
        except:
            pass

    # 3. Sync Personal Details (DOB, Sex)
    if latest_intake.get("dob"):
         doc.dob = latest_intake.get("dob")
         
    if latest_intake.get("sex"):
         # Ensure Gender link matches
         doc.sex = latest_intake.get("sex")

    # 4. Sync Mobile/Email if missing (optional, but good for completeness)
    if not doc.mobile and latest_intake.get("mobile"):
        doc.mobile = latest_intake.get("mobile")

