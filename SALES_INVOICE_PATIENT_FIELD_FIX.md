# Sales Invoice Patient Field Fix

## Problem
When viewing a Patient document, the system throws an error:
```
pymysql.err.OperationalError: (1054, "Unknown column 'tabSales Invoice.patient' in 'WHERE'")
```

This occurs because the Patient doctype has a link configured to Sales Invoice using a `patient` field, but the database column doesn't exist.

## Root Cause
The Healthcare app defines a custom `patient` field for Sales Invoice in its setup, but the field wasn't properly created in the database. This can happen if:
- The healthcare app wasn't fully installed
- Custom fields weren't migrated to the database
- The field was removed or never created

## Solution

### Immediate Fix (Error Handling)
I've updated `bench/apps/frappe/frappe/desk/notifications.py` to gracefully handle missing column errors. The system will now return a count of 0 instead of crashing when a custom field column is missing.

### Permanent Fix

#### Option 1: Run Migrate (Recommended)
The simplest solution is to run migrate, which will create any missing custom field columns:

```bash
bench --site [your-site] migrate
```

#### Option 2: Run the Fix Script
If migrate doesn't work, run the fix script:

```bash
# Via bench console
bench --site [your-site] console
```

Then in the console:
```python
exec(open('fix_sales_invoice_patient_field.py').read())
```

Or directly:
```bash
bench --site [your-site] execute fix_sales_invoice_patient_field.execute
```

#### Option 3: Manual Fix via UI
1. Go to Customize Form: `/app/customize-form?doctype=Sales Invoice`
2. Add a custom field:
   - Field Name: `patient`
   - Label: `Patient`
   - Field Type: `Link`
   - Options: `Patient`
   - Insert After: `naming_series`
3. Save
4. Run: `bench --site [your-site] migrate`

## Verification

After applying the fix, verify the field exists:

```bash
bench --site [your-site] console
```

```python
# Check if custom field exists
frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "patient"})

# Check if database column exists
frappe.db.sql("DESCRIBE `tabSales Invoice` LIKE 'patient'")
```

## Files Modified

1. `bench/apps/frappe/frappe/desk/notifications.py`
   - Added error handling for missing column errors
   - Returns 0 count instead of crashing when custom field columns are missing

2. `bench/fix_sales_invoice_patient_field.py`
   - Script to create the missing custom field if it doesn't exist

## Notes

- The error handling will prevent crashes, but the link count will show 0 until the field is created
- After creating the field, you may need to refresh your browser
- The healthcare app should have created this field during installation - if it's missing, there may be other setup issues
