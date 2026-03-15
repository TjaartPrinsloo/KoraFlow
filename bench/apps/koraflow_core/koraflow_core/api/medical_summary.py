"""
Medical Summary Generation using Ollama
Generates AI-powered medical summaries from patient intake forms
"""

import frappe
import requests
import json
from frappe import _


def generate_medical_summary(intake_data, patient_name=None):
	"""
	Generate a medical summary from patient intake form data using Ollama medllama2 model
	
	Args:
		intake_data: Dictionary containing intake form data
		patient_name: Optional patient name for context
		
	Returns:
		str: Generated medical summary or None if generation fails
	"""
	try:
		# Get Ollama configuration - try from site config, then defaults
		ollama_host = frappe.conf.get('ollama_host') or 'localhost'
		ollama_port = frappe.conf.get('ollama_port') or 11434
		medical_model = frappe.conf.get('ollama_medical_model') or 'medllama2'
		
		# Try to get from Healthcare Settings if fields exist (optional)
		try:
			healthcare_settings = frappe.get_single('Healthcare Settings')
			if hasattr(healthcare_settings, 'ollama_host') and healthcare_settings.ollama_host:
				ollama_host = healthcare_settings.ollama_host
			if hasattr(healthcare_settings, 'ollama_port') and healthcare_settings.ollama_port:
				ollama_port = healthcare_settings.ollama_port
			if hasattr(healthcare_settings, 'ollama_medical_model') and healthcare_settings.ollama_medical_model:
				medical_model = healthcare_settings.ollama_medical_model
		except:
			# Healthcare Settings fields don't exist, use defaults
			pass
		
		# Format intake data into a readable structure for the LLM
		formatted_data = format_intake_data_for_llm(intake_data, patient_name)
		
		# Create prompt for medical summary generation
		prompt = create_medical_summary_prompt(formatted_data)
		
		# Call Ollama API
		url = f"http://{ollama_host}:{ollama_port}/api/generate"
		payload = {
			"model": medical_model,
			"prompt": prompt,
			"stream": False,
			"options": {
				"temperature": 0.1,  # Low temperature for deterministic outputs
				"seed": 42,          # Fixed seed for reproducibility
				"num_ctx": 4096,     # Ensure sufficient context
				"num_predict": 1500, # Limit response length
			}
		}
		
		response = requests.post(url, json=payload, timeout=120)
		response.raise_for_status()
		
		result = response.json()
		raw_summary = result.get('response', '').strip()
		
		if raw_summary:
			# Append mandatory clinical disclaimer
			summary = f"{raw_summary}\n\n---\n**Disclaimer**: This summary is AI-generated for clinical support only. Please verify all details with the original patient records."
			
			frappe.logger().info(f"Generated medical summary for patient {patient_name or 'Unknown'}")
			return summary
		else:
			frappe.log_error(title="Medical Summary Generation", message="Empty response from Ollama medical model")
			return None
			
	except requests.exceptions.RequestException as e:
		frappe.log_error(title="Medical Summary Generation", message=f"Ollama API error: {str(e)}")
		return None
	except Exception as e:
		frappe.log_error(title="Medical Summary Generation", message=f"Error generating medical summary: {str(e)}")
		return None


def format_intake_data_for_llm(intake_data, patient_name=None):
	"""
	Format intake form data into a structured text format for LLM processing
	"""
	lines = []
	
	if patient_name:
		lines.append(f"Patient: {patient_name}")
	
	# Demographics & Vitals
	demo = []
	if intake_data.get('first_name') or intake_data.get('last_name'):
		demo.append(f"Name: {intake_data.get('first_name', '')} {intake_data.get('last_name', '')}".strip())
	if intake_data.get('dob') or intake_data.get('date_of_birth'):
		demo.append(f"DOB: {intake_data.get('dob') or intake_data.get('date_of_birth')}")
	if intake_data.get('sex') or intake_data.get('biological_sex'):
		demo.append(f"Gender: {intake_data.get('sex') or intake_data.get('biological_sex')}")
	
	vitals = []
	if intake_data.get('intake_height_cm'): vitals.append(f"Height: {intake_data.get('intake_height_cm')}cm")
	if intake_data.get('intake_weight_kg'): vitals.append(f"Weight: {intake_data.get('intake_weight_kg')}kg")
	if intake_data.get('intake_bp_systolic'): vitals.append(f"BP: {intake_data.get('intake_bp_systolic')}/{intake_data.get('intake_bp_diastolic')}")
	if intake_data.get('intake_heart_rate'): vitals.append(f"HR: {intake_data.get('intake_heart_rate')}bpm")
	
	if demo: lines.append("Demographics: " + ", ".join(demo))
	if vitals: lines.append("Vitals: " + ", ".join(vitals))

	# Section 1: Endocrine/Metabolic
	endocrine = []
	endo_map = {
		"intake_diabetes_type_1": "Type 1 Diabetes (Insulin Dependent)",
		"intake_underactive_thyroid": "Underactive Thyroid",
		"intake_thyroid_ca": "Thyroid Carcinoma/Cancer",
		"intake_family_thyroid_ca": "Family History of Thyroid Carcinoma",
		"intake_diabetic_retinopathy": "Diabetic Retinopathy",
		"intake_hypoglycaemia": "Hypoglycaemia",
		"intake_men2": "MEN 2",
		"intake_other_endocrine": "Other Endocrine Condition"
	}
	for key, label in endo_map.items():
		if intake_data.get(key) == "1" or intake_data.get(key) is True:
			endocrine.append(label)
	if intake_data.get("intake_endocrine_details"):
		endocrine.append(f"Details: {intake_data.get('intake_endocrine_details')}")
	if endocrine: lines.append("Endocrine/Metabolic: " + ", ".join(endocrine))

	# Section 2: Liver/Kidney/Digestive
	lkd = []
	lkd_map = {
		"intake_pancreatitis": "Pancreatitis",
		"intake_kidney_disease": "Kidney Disease",
		"intake_gastro_disease": "Gastrointestinal Disease",
		"intake_gastroparesis": "Gastroparesis",
		"intake_gallbladder_disease": "Gallbladder Disease",
		"intake_other_lkd": "Other LKD Condition",
		"intake_constipation": "Constipation"
	}
	for key, label in lkd_map.items():
		if intake_data.get(key) == "1" or intake_data.get(key) is True:
			lkd.append(label)
	if intake_data.get("intake_lkd_details"):
		lkd.append(f"Details: {intake_data.get('intake_lkd_details')}")
	if lkd: lines.append("Liver/Kidney/Digestive: " + ", ".join(lkd))

	# Section 3: Mental Health
	mental = []
	mental_map = {
		"intake_depression": "Depression",
		"intake_anxiety": "Anxiety",
		"intake_eating_disorder": "Eating Disorder",
		"intake_other_mental": "Other Mental Health Condition"
	}
	for key, label in mental_map.items():
		if intake_data.get(key) == "1" or intake_data.get(key) is True:
			mental.append(label)
	if intake_data.get("intake_mental_details"):
		mental.append(f"Details: {intake_data.get('intake_mental_details')}")
	if mental: lines.append("Mental Health: " + ", ".join(mental))

	# Section 4: General Medical
	general = []
	gen_map = {
		"intake_heart_disease": "Heart Disease",
		"intake_high_bp": "High Blood Pressure",
		"intake_med_allergies": "Medication Allergies",
		"intake_other_allergy": "Other Allergy"
	}
	for key, label in gen_map.items():
		if intake_data.get(key) == "1" or intake_data.get(key) is True:
			general.append(label)
	if intake_data.get("intake_general_details"):
		general.append(f"Details: {intake_data.get('intake_general_details')}")
	if general: lines.append("General Medical: " + ", ".join(general))

	# Section 5: Weight History
	weight_hist = []
	if intake_data.get("intake_weight_injectables") == "Yes":
		weight_hist.append("Prior Weight Injectables Used")
		if intake_data.get("intake_weight_date_started"): weight_hist.append(f"Started: {intake_data.get('intake_weight_date_started')}")
		if intake_data.get("intake_weight_date_stopped"): weight_hist.append(f"Stopped: {intake_data.get('intake_weight_date_stopped')}")
		if intake_data.get("intake_weight_period"): weight_hist.append(f"Period: {intake_data.get('intake_weight_period')}")
		if intake_data.get("intake_weight_highest_dose"): weight_hist.append(f"Max Dose: {intake_data.get('intake_weight_highest_dose')}")
		if intake_data.get("intake_weight_loss_kg"): weight_hist.append(f"Weight Loss: {intake_data.get('intake_weight_loss_kg')}kg")
		if intake_data.get("intake_weight_stop_reason"): weight_hist.append(f"Stop Reason: {intake_data.get('intake_weight_stop_reason')}")
	if weight_hist: lines.append("Weight Management History: " + ", ".join(weight_hist))

	# Section 6: Exercise & Other
	exercise = []
	if intake_data.get("intake_exercise_frequency"): exercise.append(f"Frequency: {intake_data.get('intake_exercise_frequency')}x/week")
	if intake_data.get("intake_exercise_aerobic"): exercise.append(f"Aerobic: {intake_data.get('intake_exercise_aerobic')}x/week")
	if intake_data.get("intake_exercise_strength"): exercise.append(f"Strength: {intake_data.get('intake_exercise_strength')}x/week")
	if exercise: lines.append("Exercise Habits: " + ", ".join(exercise))
	
	if intake_data.get("intake_other_medical_issues"):
		lines.append(f"Other Health Concerns: {intake_data.get('intake_other_medical_issues')}")

	# Section 7: Surgical History
	surgical = []
	if intake_data.get("intake_recent_gp_visit") == "Yes": surgical.append("Visited GP Recently")
	if intake_data.get("intake_abnormal_labs_recent") == "Yes": 
		surgical.append(f"Abnormal Labs: {intake_data.get('intake_abnormal_labs_details')}")
	if intake_data.get("intake_recent_op") == "Yes":
		surgical.append(f"Recent Operations: {intake_data.get('intake_recent_op_details')}")
	if intake_data.get("intake_planned_op") == "Yes":
		surgical.append(f"Planned Operations: {intake_data.get('intake_planned_op_details')}")
	if surgical: lines.append("Surgical/Clinical History: " + ", ".join(surgical))

	# Section 8: Detailed Medications
	detailed_meds = []
	med_cats = {
		"intake_diabetes_meds_list": "Diabetes Meds",
		"intake_vitamins_list": "Vitamins/Supps",
		"intake_birth_control_list": "Birth Control",
		"intake_otc_list": "OTC Meds",
		"intake_chronic_list": "Chronic Meds",
		"intake_other_meds_list": "Other Meds"
	}
	for key, label in med_cats.items():
		if intake_data.get(key):
			detailed_meds.append(f"{label}: {intake_data.get(key)}")
	if detailed_meds: lines.append("Detailed Medications: " + " | ".join(detailed_meds))

	return "\n".join(lines)


def create_medical_summary_prompt(formatted_data):
	"""
	Create a few-shot prompt for generating medical summary from intake form data
	
	Args:
		formatted_data: Formatted intake form data as text
		
	Returns:
		str: Complete prompt for LLM
	"""
	prompt = f"""You are a medical professional reviewing a patient intake form for GLP-1 medication assessment.
Your goal is to extract key clinical information and present it in a concise, structured format.

### Example Input:
Patient: Jane Doe
Gender: Female
Vital Signs: BMI 28, BP 130/85
High Risk Conditions: History of Pancreatitis
Organ System Issues: None
Current Medications: None

### Example Output:
**Patient Overview**: Jane Doe, Female.
**Key Medical History**: History of Pancreatitis (High Risk).
**Current Medications**: None reported.
**GLP-1 History**: No prior use reported.
**Contraindications & Warnings**: 
- History of pancreatitis is a potential contraindication for GLP-1s.
**Recommendations**: 
- Proceed with caution; verify cause of pancreatitis.
- Consider alternative therapies.

---

### Current Patient Input:
{formatted_data}

### Instructions:
Provide a medical summary for this patient using the EXACT structure below. Be strictly fact-based.

1. **Patient Overview**: Demographics and Vitals.
2. **Key Medical History**: Conditions and risk factors.
3. **Current Medications**: Relevant drugs.
4. **GLP-1 History**: Previous use/side effects.
5. **Contraindications & Warnings**: Flag any absolute or relative contraindications (e.g., MEN2, Pancreatitis, Pregnancy).
6. **Recommendations**: Clinical suggestions.

Medical Summary:
"""
	return prompt


def classify_bmi_rag(weight_kg, height_cm, age, sex):
	"""
	Classify BMI using RAG/LLM system to account for age and gender nuances.
	Returns a dictionary with classification and rag_color.
	"""
	try:
		# Ollama config
		ollama_host = frappe.conf.get('ollama_host') or 'localhost'
		ollama_port = frappe.conf.get('ollama_port') or 11434
		medical_model = frappe.conf.get('ollama_medical_model') or 'medllama2'
		
		prompt = f"""
		Task: Analyze BMI for a patient.
		Input:
		- Age: {age}
		- Sex: {sex}
		- Weight: {weight_kg} kg
		- Height: {height_cm} cm
		
		Instructions:
		1. Calculate BMI.
		2. determining the Clinical Category (Underweight, Normal, Overweight, Obese Class I/II/III). Consider age/sex adjustments if medically relevant (e.g. elderly).
		3. Assign a RAG Status (Red, Amber, Green). Green=Healthy, Amber=Risk/Warning, Red=High Risk.
		
		Output Format: JSON only.
		{{
			"bmi": <float>,
			"category": "<string>",
			"rag_color": "<Green|Amber|Red>",
			"reason": "<short explanation>"
		}}
		"""
		
		url = f"http://{ollama_host}:{ollama_port}/api/generate"
		payload = {
			"model": medical_model,
			"prompt": prompt,
			"stream": False,
			"format": "json", # Force JSON
			"options": {
				"temperature": 0.0,
			}
		}
		
		response = requests.post(url, json=payload, timeout=5)
		if response.status_code == 200:
			res = response.json()
			return json.loads(res.get('response', '{}'))
	except Exception as e:
		frappe.log_error(title="BMI RAG Error", message=f"BMI RAG Error: {str(e)}")
		# Fallback to standard calculation if RAG fails
		return None


