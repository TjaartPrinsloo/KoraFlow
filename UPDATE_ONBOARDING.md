# Update Module Onboarding Database Records

The text "Let's begin your journey with ERPNext" is stored in the database and needs to be updated there.

## Option 1: Manual Update via Desk UI (Easiest)

1. Log into your KoraFlow site
2. Go to **Desk** → **Module Onboarding**
3. Find and open the record named **"Home"**
4. Update the **Title** field from:
   - `Let's begin your journey with ERPNext`
   - to: `Let's begin your journey with KoraFlow`
5. Update the **Success Message** field if it contains "ERPNext"
6. Click **Save**
7. Refresh your browser

## Option 2: Direct SQL Update

If you have database access, you can run this SQL:

```sql
UPDATE `tabModule Onboarding`
SET 
    `title` = REPLACE(`title`, 'ERPNext', 'KoraFlow'),
    `success_message` = REPLACE(`success_message`, 'ERPNext', 'KoraFlow'),
    `subtitle` = REPLACE(`subtitle`, 'ERPNext', 'KoraFlow')
WHERE `name` = 'Home';
```

## Option 3: Python Script (when bench is available)

When you have access to the bench command, run:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
bench --site koraflow-site console
```

Then paste:

```python
import frappe

doc = frappe.get_doc("Module Onboarding", "Home")
if "ERPNext" in doc.title:
    doc.title = doc.title.replace("ERPNext", "KoraFlow")
if "ERPNext" in doc.success_message:
    doc.success_message = doc.success_message.replace("ERPNext", "KoraFlow")
if doc.subtitle and "ERPNext" in doc.subtitle:
    doc.subtitle = doc.subtitle.replace("ERPNext", "KoraFlow")
doc.save(ignore_permissions=True)
frappe.db.commit()
print("Updated!")
```

## Why This Is Needed

The JSON file we updated (`bench/apps/erpnext/erpnext/setup/module_onboarding/home/home.json`) is used to **create** new records, but existing database records don't automatically update when JSON files change. The widget loads data directly from the database, so the database record must be updated.

