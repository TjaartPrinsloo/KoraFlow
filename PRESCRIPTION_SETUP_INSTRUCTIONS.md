# Prescription Setup Instructions

## Steps to Complete Setup

### Step 1: Run the Patch to Add Custom Fields

Run the following command in your terminal from the bench directory:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
bench --site [your-site-name] execute koraflow_core.patches.v1_0.add_prescription_fields_to_practitioner.execute
```

Or if you have a specific site name (e.g., `koraflow-site`):

```bash
bench --site koraflow-site execute koraflow_core.patches.v1_0.add_prescription_fields_to_practitioner.execute
```

This will add the following custom fields to Healthcare Practitioner:
- `practice_number` - Practice registration number
- `hpcsa_registration_number` - HPCSA registration number  
- `practice_address` - Practice physical address
- `prescription_template` - Attach field for blank PDF template
- `prescription_print_format` - Link to Print Format

### Step 2: Import the Print Format

Import the SAHPRA Prescription print format:

```bash
bench --site [your-site-name] import-doc bench/apps/koraflow_core/koraflow_core/print_format/sahpra_prescription/sahpra_prescription.json
```

Or:

```bash
bench --site koraflow-site import-doc bench/apps/koraflow_core/koraflow_core/print_format/sahpra_prescription/sahpra_prescription.json
```

### Alternative: Use Python Script

If you prefer, you can also use the provided script (requires Python 3.10+):

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
python3 run_prescription_setup.py
```

**Note**: This script requires Python 3.10+ due to Frappe dependencies. If you're using Python 3.9, use the bench commands above instead.

## Verification

After running the setup:

1. **Check Custom Fields**: 
   - Go to Customize Form → Healthcare Practitioner
   - Verify the new fields appear in the "Prescription Settings" section

2. **Check Print Format**:
   - Go to Print Format list
   - Search for "SAHPRA Prescription"
   - Verify it exists and is linked to "Patient Encounter" doctype

## Next Steps

1. **Configure Practitioners**:
   - Open each Healthcare Practitioner record
   - Fill in:
     - Practice Number
     - HPCSA Registration Number
     - Practice Physical Address
   - Optionally upload a blank prescription template PDF
   - Optionally select a custom print format

2. **Test the Functionality**:
   - Create a Patient Encounter
   - Add medications to the encounter
   - Submit the encounter
   - Check the Patient record's attachments - you should see a prescription PDF

## Troubleshooting

If you encounter issues:

1. **Custom fields not appearing**: 
   - Clear cache: `bench --site [site-name] clear-cache`
   - Reload doctype: `bench --site [site-name] migrate`

2. **Print format not importing**:
   - Check file path is correct
   - Verify JSON file is valid
   - Try importing via UI: Setup → Data → Import

3. **Prescription not generating**:
   - Check Error Log for any errors
   - Verify encounter has medications
   - Verify practitioner has required fields filled
   - Check that print format exists
