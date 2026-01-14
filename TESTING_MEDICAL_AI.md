# Medical AI Integration - Testing Guide

## Overview

This document describes the testing implementation for the Medical AI integration with Ollama MedLlama2 model.

## Test Script

**Location**: `bench/test_medical_ai_intake_scenarios.py`

### Features

The test script includes **6 real-world patient scenarios**:

1. **Healthy Patient - Ideal Candidate**
   - Young, healthy patient with no contraindications
   - Tests baseline functionality

2. **Patient with Contraindications - Pancreatitis History**
   - History of pancreatitis (contraindication)
   - Tests AI's ability to identify contraindications

3. **Patient with Kidney Disease - eGFR Monitoring Required**
   - Kidney disease requiring careful monitoring
   - Previous GLP-1 use with side effects
   - Tests complex medical history analysis

4. **Pregnant Patient - Absolute Contraindication**
   - Currently pregnant (absolute contraindication)
   - Tests critical safety flagging

5. **Patient with MTC/MEN2 - Absolute Contraindication**
   - Medullary thyroid carcinoma history
   - Tests oncology-related contraindications

6. **Patient with Previous GLP-1 Experience - Side Effects**
   - Previous GLP-1 use with significant side effects
   - Gastroparesis development
   - Tests adverse event analysis

## Prerequisites

Before running the tests:

1. **Run the patch** to add the medical summary field:
   ```bash
   cd bench
   bench --site koraflow-site migrate
   ```

2. **Ensure Ollama is running**:
   ```bash
   ollama serve
   ```

3. **Verify MedLlama2 is installed**:
   ```bash
   ollama list | grep medllama2
   ```

## Running the Tests

### Full Test Suite

```bash
cd bench
source env/bin/activate
python3 test_medical_ai_intake_scenarios.py
```

### Single Scenario Test

You can modify the script to test a single scenario by changing:
```python
for i, scenario in enumerate(TEST_SCENARIOS, 1):
    # Change to: enumerate([TEST_SCENARIOS[0]], 1):  # Test only first scenario
```

## Expected Output

The test script will:

1. Create test users for each scenario
2. Submit intake forms with realistic medical data
3. Verify patient records are created
4. Check if AI medical summaries are generated
5. Display summary statistics

### Sample Output

```
================================================================================
MEDICAL AI INTAKE FORM - REAL-WORLD SCENARIO TESTING
================================================================================

[1/6]
Testing: Healthy Patient - Ideal Candidate
Description: Young, healthy patient with no contraindications
--------------------------------------------------------------------------------
  ✓ Created user: sarahjohnson20251230164754@test.example.com
  ✓ Created patient: PATIENT-00001
  ✓ Created intake form: abc123xyz
    ✓ Patient record: PATIENT-00001
    Status: Under Review
    Intake forms: 1
    ✓ AI Medical Summary: Generated (1250 characters)
    Preview: **Patient Overview**: Sarah Johnson, 34-year-old female...

[2/6]
...

================================================================================
TEST SUMMARY
================================================================================
Total Scenarios: 6
Successful: 6
Failed: 0

AI Medical Summaries Generated: 6/6

Detailed Results:
  ✓ [1] Healthy Patient - Ideal Candidate - Summary: ✓
  ✓ [2] Patient with Contraindications - Pancreatitis History - Summary: ✓
  ...
```

## Troubleshooting

### AI Summary Not Generated

If summaries are not being generated:

1. **Check Ollama Service**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check Frappe Error Log**:
   - Navigate to: Setup > Logs > Error Log
   - Look for "Medical Summary Generation" errors

3. **Verify Field Exists**:
   ```python
   import frappe
   frappe.init(site='koraflow-site')
   frappe.connect()
   meta = frappe.get_meta('Patient')
   print('ai_medical_summary field exists:', meta.get_field('ai_medical_summary') is not None)
   ```

### User Creation Errors

If you see user creation errors, the test script uses SQL to bypass hooks. If issues persist:

1. Check database permissions
2. Verify User doctype is accessible
3. Check for duplicate email addresses

## Browser Testing

### Manual Testing Steps

1. **Navigate to Intake Form**:
   - URL: `http://localhost:8000/glp1-intake`
   - Login as a test user

2. **Fill Out Form**:
   - Complete all required fields
   - Use realistic medical data from the test scenarios

3. **Submit Form**:
   - Click "Submit Intake Form"
   - Verify success message

4. **Check Patient Record**:
   - Navigate to: Desk > Patient
   - Open the created patient record
   - Scroll to "AI Medical Summary" field
   - Verify summary is generated

### Automated Browser Testing

For automated browser testing, you can use:

```python
from selenium import webdriver
# Or use the browser MCP tools available in Cursor
```

## Test Data

Each scenario includes:

- **Demographics**: Name, DOB, gender, contact info
- **Vital Signs**: Height, weight, BP, heart rate
- **Medical History**: Conditions, organ system issues
- **Medications**: Current medications
- **GLP-1 History**: Previous use, doses, side effects
- **Reproductive Health**: Pregnancy status, etc.

## Integration with CI/CD

To integrate into CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Test Medical AI Integration
  run: |
    cd bench
    source env/bin/activate
    python3 test_medical_ai_intake_scenarios.py
```

## Next Steps

1. **Add More Scenarios**: Expand test coverage with additional medical conditions
2. **Performance Testing**: Test with multiple concurrent submissions
3. **Summary Quality Testing**: Validate AI summary accuracy and completeness
4. **Error Handling**: Test error scenarios (Ollama down, network issues, etc.)

## Notes

- Test users are created with unique emails to avoid conflicts
- All test data is marked with timestamps for uniqueness
- Patient records are created with "Under Review" status
- AI summaries are generated asynchronously (non-blocking)

