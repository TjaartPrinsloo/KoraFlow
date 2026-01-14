# Medical AI Integration - Ollama MedLlama2

## Overview

This integration adds AI-powered medical summary generation to the KoraFlow healthcare app. When a patient submits an intake form, the system automatically generates a comprehensive medical summary using the Ollama MedLlama2 model, which helps medical staff quickly review patient profiles, identify contraindications, and make informed decisions.

## Components

### 1. Medical Summary Generation (`medical_summary.py`)
- **Location**: `bench/apps/koraflow_core/koraflow_core/api/medical_summary.py`
- **Function**: `generate_medical_summary(intake_data, patient_name)`
- Generates AI-powered medical summaries from patient intake form data
- Uses Ollama MedLlama2 model for medical-specific analysis
- Formats intake data into structured prompts for the LLM

### 2. Patient DocType Enhancement
- **Patch**: `add_medical_summary_field_to_patient.py`
- Adds `ai_medical_summary` field to Patient doctype
- Field type: Text Editor (read-only)
- Automatically populated when intake form is submitted

### 3. Integration with Intake Form Submission
- **File**: `bench/apps/koraflow_core/koraflow_core/api/patient_signup.py`
- Automatically generates medical summary after patient creation
- Summary is saved to Patient record for medical staff review

## Features

The AI-generated medical summary includes:

1. **Patient Overview**: Demographics and vital signs summary
2. **Key Medical History**: Relevant medical conditions, organ system issues, and risk factors
3. **Current Medications**: Medications that may interact with GLP-1 medications
4. **GLP-1 History**: Previous GLP-1 medication use and experiences
5. **Contraindications & Warnings**: 
   - Conditions that may contraindicate GLP-1 medication use
   - Drug interactions to be aware of
   - Special precautions needed
6. **Recommendations**: 
   - Suggested next steps for medical staff review
   - Areas requiring further investigation
   - Potential concerns or red flags

## Setup

### Prerequisites

1. **Ollama Service**: Must be running on localhost:11434 (or configured host/port)
2. **MedLlama2 Model**: Must be installed via `ollama pull medllama2`

### Installation Steps

1. **Pull the MedLlama2 model**:
   ```bash
   ollama pull medllama2
   ```

2. **Run the patch** to add the medical summary field:
   ```bash
   cd bench
   bench --site [site-name] migrate
   ```

3. **Verify Ollama is accessible**:
   - Default: `http://localhost:11434`
   - Can be configured via site config or Healthcare Settings

## Configuration

### Ollama Configuration

The system looks for Ollama configuration in this order:
1. Site config (`frappe.conf`)
2. Healthcare Settings (if available)
3. Defaults: `localhost:11434` with model `medllama2`

### Site Config Example

Add to `sites/[site-name]/site_config.json`:
```json
{
  "ollama_host": "localhost",
  "ollama_port": 11434,
  "ollama_medical_model": "medllama2"
}
```

## Usage

### Automatic Generation

Medical summaries are automatically generated when:
- A patient submits an intake form via `create_patient_from_intake()`
- The intake form data is successfully saved to the Patient record

### Manual Generation (Future Enhancement)

You can manually trigger summary generation by calling:
```python
from koraflow_core.api.medical_summary import generate_medical_summary

summary = generate_medical_summary(intake_data, patient_name="PATIENT-00001")
```

## Viewing Medical Summaries

1. Navigate to a Patient record in the KoraFlow Healthcare app
2. Scroll to the "AI Medical Summary" field (located after GLP-1 Intake Forms)
3. Review the generated summary for:
   - Patient overview
   - Medical history highlights
   - Contraindications
   - Recommendations for medical staff

## Error Handling

- If Ollama is unavailable, patient creation still succeeds (summary generation is non-blocking)
- Errors are logged to Frappe error log for debugging
- Medical summary field will remain empty if generation fails

## Model Information

- **Model**: MedLlama2
- **Size**: ~3.8 GB
- **Purpose**: Medical question answering and medical text analysis
- **Temperature**: 0.3 (lower for more focused, medical-accurate summaries)
- **Max Tokens**: 1500 (sufficient for comprehensive summaries)

## Security & Privacy

- All processing happens locally via Ollama (no external API calls)
- Patient data remains on-premises
- Medical summaries are stored in the Patient record with standard Frappe permissions
- Access controlled by Frappe's role-based permission system

## Troubleshooting

### Summary Not Generated

1. **Check Ollama Service**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Verify Model is Installed**:
   ```bash
   ollama list | grep medllama2
   ```

3. **Check Frappe Error Log**:
   - Navigate to: Setup > Logs > Error Log
   - Look for "Medical Summary Generation" errors

### Ollama Connection Issues

- Ensure Ollama service is running: `ollama serve`
- Check firewall settings if using remote Ollama instance
- Verify host/port configuration in site config

## Future Enhancements

- [ ] Manual regeneration of summaries
- [ ] Summary versioning/history
- [ ] Customizable prompt templates
- [ ] Integration with other medical models
- [ ] Summary comparison between intake form versions
- [ ] Export summaries to PDF for medical records

## Support

For issues or questions:
1. Check Frappe error logs
2. Verify Ollama service status
3. Review patient intake form data completeness
4. Contact KoraFlow support team

