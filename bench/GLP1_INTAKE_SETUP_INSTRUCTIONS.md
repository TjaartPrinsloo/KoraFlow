# GLP-1 Intake Form Setup Instructions

## Step 1: Run the Patch to Add Custom Field

The patch adds the `glp1_intake_forms` child table field to the Patient DocType.

### Option A: Using Bench Migrate (Recommended)
```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
bench --site koraflow-site migrate
```

### Option B: Run Patch Manually
```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
bench --site koraflow-site console
```

Then in the console:
```python
from koraflow_core.koraflow_core.patches.v1_0.add_glp1_intake_field_to_patient import execute
execute()
frappe.db.commit()
```

### Option C: Using Python Script
```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
source env/bin/activate
python3 run_patch.py
```

## Step 2: Verify Custom Field Was Added

1. Go to Desk → Customize → Customize Form
2. Select DocType: **Patient**
3. Look for the field **"GLP-1 Intake Forms"** in the field list
4. It should appear after the "Medical History" tab

## Step 3: Access the Form Builder

1. Go to Desk → Web Form
2. Find or create the Web Form named **"glp1-intake"**
3. Click Edit to open the Form Builder
4. You can now customize the form fields using the visual builder

## Step 4: Verify Intake Form Route

The intake form should be accessible at:
- **URL**: `/glp1-intake`
- **Template**: `templates/pages/glp1_intake.html`

To test:
1. Login as a user who doesn't have a Patient record
2. You should be automatically redirected to `/glp1-intake`
3. Or manually navigate to `/glp1-intake` after login

## Step 5: Test the Complete Flow

1. **Create a new user** (or use an existing user without a Patient record)
2. **Login** as that user
3. **Verify redirect**: You should be redirected to `/glp1-intake`
4. **Fill out the form**: Complete all sections of the intake form
5. **Submit**: Click "Submit Intake Form"
6. **Verify creation**: 
   - A Patient record should be created
   - A GLP-1 Intake Form child record should be linked to the Patient
   - You should be redirected to `/app/patient`

## Files Created

### DocTypes
- `koraflow_core/doctype/glp1_intake_form/` - Child table DocType

### API Methods
- `koraflow_core/api/patient_signup.py` - Patient creation and intake form management

### Web Form
- `koraflow_core/web_form/glp1_intake/` - Web Form configuration

### Templates
- `koraflow_core/templates/pages/glp1_intake.html` - Custom HTML template

### JavaScript
- `koraflow_core/public/js/intake_form_redirect.js` - Auto-redirect logic

### Patches
- `koraflow_core/patches/v1_0/add_glp1_intake_field_to_patient.py` - Custom field patch

## Troubleshooting

### Custom Field Not Appearing
- Run the patch again: `bench --site koraflow-site migrate`
- Check if patch was executed: Look in `sites/koraflow-site/patches.txt` or check Custom Field list

### Form Not Accessible
- Check Web Form is published: Desk → Web Form → glp1-intake → Ensure "Published" is checked
- Verify route: Should be `/glp1-intake`
- Check permissions: Ensure user has access to Web Form

### Redirect Not Working
- Clear browser cache
- Check JavaScript console for errors
- Verify `intake_form_redirect.js` is loaded (check Network tab)

### Patient Not Created
- Check API method permissions
- Verify user email matches
- Check Frappe logs for errors

## Next Steps

1. **Customize the Form**: Use the Form Builder to adjust fields, layout, and validation
2. **Add Validation**: Enhance the Python validation in `glp1_intake_form.py`
3. **Style the Form**: Customize the HTML template styling
4. **Add Notifications**: Set up email notifications when intake form is submitted
5. **Create Reports**: Build reports based on intake form data

