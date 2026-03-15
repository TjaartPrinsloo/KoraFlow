import frappe
from frappe import _

def sync_intake_to_patient(doc, method):
    """
    Syncs data from the latest GLP-1 Intake Form (child table) to the Patient parent fields.
    Hooked to Patient.before_save
    """
    # Find the most recent standalone intake submission linked to this patient
    latest_intakes = frappe.get_all(
        "GLP-1 Intake Submission",
        filters={"patient": doc.name},
        fields=["*"],
        order_by="creation desc",
        limit_page_length=1
    )
    
    if not latest_intakes:
        return
        
    latest_intake = latest_intakes[0]
    
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
            doc.uid = new_uid

    # Sync specific SA ID field
    if sa_id:
         # Check if field exists ("custom_sa_id_number" per patch)
         if hasattr(doc, "custom_sa_id_number") or "custom_sa_id_number" in doc.as_dict():
             doc.custom_sa_id_number = sa_id
         # Also try "sa_id_number" if custom field naming was different
         elif hasattr(doc, "sa_id_number") or "sa_id_number" in doc.as_dict():
             doc.sa_id_number = sa_id

    # 2. Sync Personal Details (DOB, Sex, Blood Group, Mobile, Last Name)
    if latest_intake.get("dob"):
        doc.dob = latest_intake.get("dob")
        
    if latest_intake.get("sex"):
        doc.sex = latest_intake.get("sex")

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
            doc.blood_group = final_bg
            
    if latest_intake.get("mobile"):
        doc.mobile = latest_intake.get("mobile")
        
    if latest_intake.get("last_name"):
        doc.last_name = latest_intake.get("last_name")

    if latest_intake.get("custom_referrer_name"):
        doc.custom_referrer_name = latest_intake.get("custom_referrer_name")

    # 3. Sync Vitals (Weight, Height, BMI, Goal Weight)
    # Fields on Patient created by add_patient_fields.py are:
    # intake_weight_kg, intake_height_cm, bmi
    
    # Weight
    if latest_intake.get("intake_weight_kg"):
         doc.intake_weight_kg = latest_intake.get("intake_weight_kg")
             
    # Height
    if latest_intake.get("intake_height_cm"):
         doc.intake_height_cm = latest_intake.get("intake_height_cm")

    # Goal Weight
    if latest_intake.get("intake_goal_weight"):
        # Fieldname guess: intake_goal_weight or goal_weight
        if hasattr(doc, "intake_goal_weight") or "intake_goal_weight" in doc.as_dict():
            doc.intake_goal_weight = latest_intake.get("intake_goal_weight")
        elif hasattr(doc, "goal_weight") or "goal_weight" in doc.as_dict():
            doc.goal_weight = latest_intake.get("intake_goal_weight")

    # BMI
    if latest_intake.get("intake_weight_kg") and latest_intake.get("intake_height_cm"):
        try:
            wt = float(latest_intake.get("intake_weight_kg"))
            ht = float(latest_intake.get("intake_height_cm"))
            if ht > 0:
                bmi = wt / ((ht/100) ** 2)
                doc.bmi = round(bmi, 1)
        except:
            pass

    # 3. Sync Personal Details (DOB, Sex)
    if latest_intake.get("dob"):
         doc.dob = latest_intake.get("dob")
         
    if latest_intake.get("sex"):
         # Ensure Gender link matches
         doc.sex = latest_intake.get("sex")

    if not doc.mobile and latest_intake.get("mobile"):
        doc.mobile = latest_intake.get("mobile")

    # 4. Summarize Categorized Medical Information into Patient History Fields
    med_history = []
    
    # Endocrine
    endo = []
    endo_fields = ["intake_diabetes_type_1", "intake_underactive_thyroid", "intake_thyroid_ca", "intake_family_thyroid_ca", "intake_diabetic_retinopathy", "intake_hypoglycaemia", "intake_men2", "intake_other_endocrine"]
    for f in endo_fields:
        if latest_intake.get(f): endo.append(f.replace("intake_", "").replace("_", " ").title())
    if endo: med_history.append("Endocrine/Metabolic: " + ", ".join(endo))
    if latest_intake.get("intake_endocrine_details"): med_history.append(f"Endocrine Details: {latest_intake.intake_endocrine_details}")

    # LKD
    lkd = []
    lkd_fields = ["intake_pancreatitis", "intake_kidney_disease", "intake_gastro_disease", "intake_gastroparesis", "intake_gallbladder_disease", "intake_other_lkd", "intake_constipation"]
    for f in lkd_fields:
        if latest_intake.get(f): lkd.append(f.replace("intake_", "").replace("_", " ").title())
    if lkd: med_history.append("Liver/Kidney/Digestive: " + ", ".join(lkd))
    if latest_intake.get("intake_lkd_details"): med_history.append(f"LKD Details: {latest_intake.intake_lkd_details}")

    # Mental Health
    mental = []
    mental_fields = ["intake_depression", "intake_anxiety", "intake_eating_disorder", "intake_other_mental"]
    for f in mental_fields:
        if latest_intake.get(f): mental.append(f.replace("intake_", "").replace("_", " ").title())
    if mental: med_history.append("Mental Health: " + ", ".join(mental))

    # General Med
    gen = []
    gen_fields = ["intake_heart_disease", "intake_high_bp", "intake_med_allergies", "intake_other_allergy"]
    for f in gen_fields:
        if latest_intake.get(f): gen.append(f.replace("intake_", "").replace("_", " ").title())
    if gen: med_history.append("General Medical: " + ", ".join(gen))

    if med_history:
        doc.medical_history = "\n".join(med_history)

    if surg_history:
        doc.surgical_history = "\n".join(surg_history)

    # Surgical History sync
    surg_history = []
    if latest_intake.get("intake_recent_gp_visit") == "Yes": surg_history.append("Recent GP Visit")
    if latest_intake.get("intake_abnormal_labs_recent") == "Yes": surg_history.append(f"Abnormal Labs: {latest_intake.intake_abnormal_labs_details}")
    if latest_intake.get("intake_recent_op") == "Yes": surg_history.append(f"Recent Op: {latest_intake.intake_recent_op_details}")
    if latest_intake.get("intake_planned_op") == "Yes": surg_history.append(f"Planned Op: {latest_intake.intake_planned_op_details}")
    
    if surg_history:
        doc.surgical_history = "\n".join(surg_history)

    # 5. Sync Address
    if latest_intake.get("address_line1"):
        doc.address_line1 = latest_intake.get("address_line1")
    if latest_intake.get("address_line2"):
        doc.address_line2 = latest_intake.get("address_line2")
    if latest_intake.get("city"):
        doc.city = latest_intake.get("city")
    if latest_intake.get("state"):
        doc.state = latest_intake.get("state")
    if latest_intake.get("pincode"):
        doc.zip_code = latest_intake.get("pincode")
    if latest_intake.get("country"):
        doc.custom_country = latest_intake.get("country")

    # 6. Sync Medication History
    # Medications might not be loaded on the row object if it's a child row
    meds = latest_intake.get("medications")
    if not meds and latest_intake.name:
        meds = frappe.get_all("Patient Medication Entry",
            filters={"parent": latest_intake.name, "parenttype": "GLP-1 Intake Submission"},
            fields=["*"])

    if meds:
        # Clear existing custom medications to avoid duplicates if re-syncing
        doc.set("custom_medication_history", [])
        for med in meds:
            doc.append("custom_medication_history", {
                "medication": med.get("medication"),
                "dosage": med.get("dosage"),
                "frequency": med.get("frequency"),
                "status": med.get("status"),
                "stopped_date": med.get("stopped_date"),
                "reason_for_stopping": med.get("reason_for_stopping")
            })

