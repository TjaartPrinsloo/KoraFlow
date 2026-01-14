# Prescription Auto-Fill System - Status

## ✅ Implementation Complete

The virtual prescription auto-fill system has been successfully implemented and is working.

## Current Status

### ✅ What's Working

1. **Custom Fields Added to Healthcare Practitioner**:
   - Practice Number
   - HPCSA Registration Number
   - Practice Physical Address
   - Blank Prescription Template (Attach field)
   - Prescription Print Format (Link field)

2. **SAHPRA Prescription Print Format Created**:
   - Print Format: "SAHPRA Prescription"
   - Includes all required SAHPRA fields
   - Jinja template with auto-fill from encounter data

3. **Prescription Generation Hook Registered**:
   - Automatically triggers on Patient Encounter submit
   - Generates prescription when medications are present

4. **Prescription File Generation**:
   - ✅ **Currently working**: Generates and attaches HTML prescription files
   - ⚠️ **PDF generation**: Requires system dependencies (see below)

### ⚠️ PDF Generation Note

The system currently generates **HTML prescription files** because PDF conversion dependencies are not installed. The HTML files contain all the prescription information and can be:
- Viewed in a browser
- Printed to PDF from the browser
- Converted to PDF once dependencies are installed

### To Enable PDF Generation

Install one of the following:

**Option 1: Install wkhtmltopdf (Recommended)**
```bash
# macOS
brew install wkhtmltopdf

# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# After installation, restart Frappe
bench restart
```

**Option 2: Install WeasyPrint Dependencies**
```bash
# macOS
brew install pango gdk-pixbuf libffi

# Ubuntu/Debian
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```

Once installed, the system will automatically generate PDF files instead of HTML.

## Testing

### Tested Successfully

✅ Prescription generated for encounter: `HLC-ENC-2026-00001`
✅ File attached to patient: `Petrus prins`
✅ File: `Prescription_HLC-ENC-2026-00001_2026-01-12*.html`
✅ File URL: `/files/Prescription_HLC-ENC-2026-00001_2026-01-12*.html`

### How to Test

1. **Create a new Patient Encounter**:
   - Add medications to the encounter
   - Submit the encounter
   - Check Patient record attachments

2. **For existing encounters** (submitted before hook was registered):
   - The prescription can be manually generated
   - Or create a new encounter to test automatic generation

## File Location

The prescription file is attached to the Patient record and can be found:
- In the Patient form under "Attachments" section
- File name format: `Prescription_{encounter_name}_{date}.html` (or `.pdf` once dependencies installed)

## Next Steps

1. **Install PDF dependencies** (optional, for PDF generation):
   ```bash
   brew install wkhtmltopdf
   bench restart
   ```

2. **Configure Healthcare Practitioners**:
   - Fill in practice details (practice number, HPCSA registration, address)
   - Optionally upload blank prescription template PDFs
   - Optionally select custom print formats

3. **Test with new encounters**:
   - Create Patient Encounter
   - Add medications
   - Submit encounter
   - Verify prescription appears in Patient attachments

## Troubleshooting

### Prescription not generating on encounter submit

1. **Check Error Log**: Go to Error Log and look for "Prescription Generation Error"
2. **Verify hook is registered**: Check `bench/apps/koraflow_core/koraflow_core/hooks.py` - should have Patient Encounter on_submit hook
3. **Check encounter has medications**: Prescription only generates if `drug_prescription` table has entries
4. **Verify practitioner exists**: Encounter must have a practitioner linked

### File not visible in Patient attachments

1. **Refresh the page**: Sometimes attachments need a refresh to appear
2. **Check file URL**: The file should be accessible at the URL shown in the File record
3. **Verify patient name matches**: File is attached to the exact patient name from the encounter

### PDF generation fails

- Install wkhtmltopdf or weasyprint dependencies (see above)
- System will automatically fall back to HTML generation if PDF fails
- HTML files contain all the same information and can be printed to PDF from browser
