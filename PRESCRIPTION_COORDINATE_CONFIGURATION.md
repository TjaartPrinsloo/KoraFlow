# Prescription PDF Template Coordinate Configuration

## Overview

The prescription system now uses your uploaded PDF template as the base and overlays the prescription data on top. This preserves your exact template design.

## Current Status

✅ **PDF Template Filling is Working**
- Your PDF template is being used as the base
- Data is being overlaid on the template
- The design from your PDF is preserved

⚠️ **Coordinate Adjustment Needed**
- The text overlay coordinates are currently set to default/example values
- You may need to adjust coordinates to match your specific PDF template layout

## How It Works

1. **PDF Template**: Your uploaded PDF template ("Slim 2 Well Prescription Template - Dr Andre Terblanche.pdf") is used as the base
2. **Data Overlay**: Prescription data (patient info, medications, etc.) is overlaid as text on top of your template
3. **Coordinate System**: Text positions are defined using PDF coordinates (points)
   - Origin (0,0) is at the **bottom-left** corner
   - X increases to the right
   - Y increases upward
   - A4 page is typically 595 x 842 points

## Adjusting Coordinates

### Option 1: Edit Default Coordinates

Edit the file: `bench/apps/koraflow_core/koraflow_core/utils/prescription_coordinates.py`

Modify the `get_default_coordinates()` function to match your PDF template layout.

### Option 2: Use a PDF Coordinate Tool

1. Open your PDF template in a PDF editor (Adobe Acrobat, Preview, etc.)
2. Note the positions where you want text to appear
3. Convert measurements to PDF points:
   - 1 inch = 72 points
   - Example: 2 inches from left = 144 points (x = 144)
   - Example: 1 inch from bottom = 72 points (y = 72)

### Option 3: Test and Adjust

1. Generate a prescription PDF
2. Check where text appears
3. Adjust coordinates in `prescription_coordinates.py`
4. Regenerate to test

## Coordinate Fields

The following fields can be positioned:

- `patient_name` - Patient full name
- `patient_id` - Patient ID number
- `patient_age` - Patient age
- `patient_gender` - Patient gender
- `practitioner_name` - Doctor name
- `practice_number` - Practice number
- `hpcsa_registration` - HPCSA registration number
- `date` - Prescription date
- `medications` - Medication list (with sub-coordinates for name, dosage, instructions)

## Example Coordinate Configuration

```python
{
    'patient_name': {'x': 100, 'y': 750, 'max_length': 50},
    'patient_id': {'x': 100, 'y': 730, 'max_length': 20},
    # ... etc
}
```

## Testing

After adjusting coordinates:

1. Generate a new prescription from an encounter
2. Check the PDF to see if text is in the correct positions
3. Adjust coordinates as needed
4. Repeat until alignment is correct

## Current Prescription

A prescription PDF has been generated using your template:
- **File**: `Prescription_HLC-ENC-2026-00001_2026-01-12*.pdf`
- **Patient**: Petrus prins
- **Status**: Uses your PDF template design

Check the file to see if text positions need adjustment.
