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
			frappe.log_error("Empty response from Ollama medical model", "Medical Summary Generation")
			return None
			
	except requests.exceptions.RequestException as e:
		frappe.log_error(f"Ollama API error: {str(e)}", "Medical Summary Generation")
		return None
	except Exception as e:
		frappe.log_error(f"Error generating medical summary: {str(e)}", "Medical Summary Generation")
		return None


def format_intake_data_for_llm(intake_data, patient_name=None):
	"""
	Format intake form data into a structured text format for LLM processing
	
	Args:
		intake_data: Dictionary containing intake form data
		patient_name: Optional patient name
		
	Returns:
		str: Formatted text representation of intake data
	"""
	lines = []
	
	if patient_name:
		lines.append(f"Patient: {patient_name}")
	
	# Demographics
	if intake_data.get('first_name') or intake_data.get('last_name'):
		name = f"{intake_data.get('first_name', '')} {intake_data.get('last_name', '')}".strip()
		if name:
			lines.append(f"Name: {name}")
	
	if intake_data.get('dob'):
		lines.append(f"Date of Birth: {intake_data.get('dob')}")
	
	if intake_data.get('sex') or intake_data.get('biological_sex'):
		sex = intake_data.get('sex') or intake_data.get('biological_sex')
		lines.append(f"Gender: {sex}")
	
	# Vital Signs
	vitals = []
	if intake_data.get('intake_height_feet') and intake_data.get('intake_height_inches'):
		vitals.append(f"Height: {intake_data.get('intake_height_feet')}'{intake_data.get('intake_height_inches')}\"")
	elif intake_data.get('intake_height_cm'):
		vitals.append(f"Height: {intake_data.get('intake_height_cm')} cm")
	
	if intake_data.get('intake_weight_pounds'):
		vitals.append(f"Weight: {intake_data.get('intake_weight_pounds')} lbs")
	elif intake_data.get('intake_weight_kg'):
		vitals.append(f"Weight: {intake_data.get('intake_weight_kg')} kg")
	
	if intake_data.get('intake_bp_systolic') and intake_data.get('intake_bp_diastolic'):
		vitals.append(f"Blood Pressure: {intake_data.get('intake_bp_systolic')}/{intake_data.get('intake_bp_diastolic')}")
	
	if intake_data.get('intake_heart_rate'):
		vitals.append(f"Heart Rate: {intake_data.get('intake_heart_rate')} bpm")
	
	if vitals:
		lines.append("Vital Signs: " + ", ".join(vitals))
	
	# High Risk Conditions
	high_risk = []
	if intake_data.get('intake_mtc'):
		high_risk.append("Multiple Endocrine Neoplasia Type 2 (MEN2)")
	if intake_data.get('intake_pancreatitis'):
		high_risk.append("History of Pancreatitis")
	if intake_data.get('intake_gallstones'):
		high_risk.append("Gallstones")
	if intake_data.get('intake_gallbladder_removal'):
		high_risk.append("Gallbladder Removal")
	if intake_data.get('intake_gastroparesis'):
		high_risk.append("Gastroparesis")
	if intake_data.get('intake_frequent_nausea'):
		high_risk.append("Frequent Nausea")
	if intake_data.get('intake_early_fullness'):
		high_risk.append("Early Fullness")
	
	if high_risk:
		lines.append("High Risk Conditions: " + ", ".join(high_risk))
	
	# Organ Systems
	organ_issues = []
	if intake_data.get('intake_kidney_disease'):
		organ_issues.append("Kidney Disease")
		if intake_data.get('intake_egfr'):
			organ_issues.append(f"eGFR: {intake_data.get('intake_egfr')}")
		if intake_data.get('intake_creatinine'):
			organ_issues.append(f"Creatinine: {intake_data.get('intake_creatinine')}")
	if intake_data.get('intake_diabetic_retinopathy'):
		organ_issues.append("Diabetic Retinopathy")
	if intake_data.get('intake_heart_attack'):
		organ_issues.append("History of Heart Attack")
	if intake_data.get('intake_stroke'):
		organ_issues.append("History of Stroke")
	if intake_data.get('intake_heart_failure'):
		organ_issues.append("Heart Failure")
	
	if organ_issues:
		lines.append("Organ System Issues: " + ", ".join(organ_issues))
	
	# Medications
	medications = []
	if intake_data.get('intake_taking_insulin'):
		medications.append("Insulin")
		if intake_data.get('intake_insulin_dose'):
			medications.append(f"Insulin Dose: {intake_data.get('intake_insulin_dose')}")
	if intake_data.get('intake_taking_sulfonylureas'):
		medications.append("Sulfonylureas")
	if intake_data.get('intake_narrow_window_drugs'):
		medications.append("Narrow Therapeutic Window Drugs")
	
	if medications:
		lines.append("Current Medications: " + ", ".join(medications))
	
	# GLP-1 History
	glp1_history = []
	if intake_data.get('intake_med_ozempic'):
		glp1_history.append("Ozempic")
	if intake_data.get('intake_med_wegovy'):
		glp1_history.append("Wegovy")
	if intake_data.get('intake_med_mounjaro'):
		glp1_history.append("Mounjaro")
	if intake_data.get('intake_med_zepbound'):
		glp1_history.append("Zepbound")
	if intake_data.get('intake_highest_dose'):
		glp1_history.append(f"Highest Dose: {intake_data.get('intake_highest_dose')}")
	if intake_data.get('intake_last_dose_date'):
		glp1_history.append(f"Last Dose Date: {intake_data.get('intake_last_dose_date')}")
	
	if glp1_history:
		lines.append("GLP-1 Medication History: " + ", ".join(glp1_history))
	
	# Side Effects
	side_effects = []
	if intake_data.get('intake_se_nausea'):
		side_effects.append("Nausea")
	if intake_data.get('intake_se_vomiting'):
		side_effects.append("Vomiting")
	if intake_data.get('intake_se_diarrhea'):
		side_effects.append("Diarrhea")
	if intake_data.get('intake_se_constipation'):
		side_effects.append("Constipation")
	if intake_data.get('intake_se_reflux'):
		side_effects.append("Reflux")
	if intake_data.get('intake_se_severity'):
		side_effects.append(f"Severity: {intake_data.get('intake_se_severity')}")
	
	if side_effects:
		lines.append("Reported Side Effects: " + ", ".join(side_effects))
	
	# Reproductive Health
	reproductive = []
	if intake_data.get('intake_pregnant'):
		reproductive.append("Currently Pregnant")
	if intake_data.get('intake_breastfeeding'):
		reproductive.append("Currently Breastfeeding")
	if intake_data.get('intake_planning_conceive'):
		reproductive.append("Planning to Conceive")
	
	if reproductive:
		lines.append("Reproductive Health: " + ", ".join(reproductive))
	
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

