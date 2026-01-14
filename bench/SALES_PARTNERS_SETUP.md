# Sales Partners Setup Script

This script creates Sales Partner records and User accounts for 3rd party sales agents with **secure, compliant permissions**.

## 🔐 Security & Compliance

Sales Partners are configured with **strict security** to ensure compliance, especially with Schedule 4 medications:

✅ **CAN see:** Only their own commission data (via User Permissions)  
❌ **CANNOT see:** Patients, Invoices, Prescriptions, Stock, Desk access

### Architecture

1. **User Type:** Website User (Portal User, NOT System User)
   - Prevents Desk access
   - Prevents ERP configuration access
   - Prevents Healthcare module access

2. **Role:** Sales Partner Portal
   - Single-purpose role
   - Read-only access to commission data only

3. **Data Isolation:** User Permissions
   - Each partner can ONLY see records where `sales_partner = themselves`
   - Applied to all doctypes automatically
   - Non-negotiable security requirement

## What it does

1. Creates a **Sales Partner** record for each agent name
2. Creates a **User account** for each sales partner with:
   - Email address generated from name (firstname.lastname@koraflow.com)
   - Secure random password
   - Sales User role assigned
3. Saves all credentials to `sales_partner_credentials.txt`

## Setup Process

### Step 1: Create Sales Partners and Users

```bash
cd bench
source env/bin/activate
python3 create_sales_partners.py
```

This creates:
- Sales Partner records
- User accounts (as Website Users)
- User Permissions for data isolation

### Step 2: Setup Role and Permissions (CRITICAL)

```bash
python3 setup_sales_partner_permissions.py
```

This:
- Creates "Sales Partner Portal" role
- Blocks access to sensitive doctypes (Patient, Invoice, Stock, etc.)
- Grants read-only access to commission data
- Updates existing users

### Step 3: Update Existing Users (if needed)

If you have existing sales partner users created before this security setup:

```bash
python3 update_existing_sales_partners.py
```

This updates:
- User type: System User → Website User
- Role: Sales User → Sales Partner Portal
- Ensures User Permissions are set up

## Output

The script will:
- Print progress to console
- Show summary of created/skipped/failed records
- Save credentials to `bench/sales_partner_credentials.txt`

## Sales Partners Created

The script creates sales partners for the following 46 agents:

- Adri Kotze
- Anita Graham
- Anke Balt
- Anna Maria Hattingh
- Annamarie Louw
- Anzel van der Merwe
- Belinda Scharneck
- Carike van Vuuren
- Chané van Biljon
- Chantelle Meyer
- Charnice Venter
- Cherise Delport
- Christelle van Wyk
- Clarissa Human
- Elmee Ellerbeck
- Erika du Toit (Potch Diet Clinic)
- Jacky de Jager
- Janine Cronje
- Jean Breedt (Bodylab Potch)
- Jeanne-Mari Uys
- Jorine Rich
- Karin Ferreira
- Le-Lue van der Sandt
- Liani Rossouw
- Liezel Swart
- Lizette Enslin
- Lizette Labuschagne
- Madie Strydom
- Marisa Vorster
- Marizelle de Beer
- Marli de Villiers
- Michelle Potgieter
- Monica Swanepoel
- Monya Oosthuizen
- Petro Enslin
- Reta Britz
- Riëtte Viljoen
- Salomé Gouws
- Seanari Sharneck
- Sone Bosman
- Sonette Viljoen
- Teneil Bierman
- Terrence Abrahams
- Theresa Visser
- Zell Lombard
- Zelmé de Villiers

## Requirements

- Sales Partner requires:
  - `partner_name` (required)
  - `territory` (required) - script uses "All Territories" or creates it if needed
  - `commission_rate` (required) - defaults to 0.0

- User requires:
  - `email` (required) - auto-generated
  - `first_name` (required) - extracted from full name
  - `user_type` - set to **"Website User"** (Portal User, NOT System User)
  - Role: **"Sales Partner Portal"** (NOT Sales User)
  - User Permission: Sales Partner = their own partner name (for data isolation)

## Notes

- The script will skip records that already exist
- Email addresses are generated from names and may have numbers appended if duplicates are detected
- Passwords are randomly generated (12 characters)
- Welcome emails are disabled for new users
- All operations use `ignore_permissions=True` to run as Administrator

## 🔒 Security Features

### Blocked Access
- ❌ Patient records
- ❌ Patient Encounters
- ❌ Medications/Prescriptions
- ❌ Sales Invoices
- ❌ Stock/Inventory
- ❌ Desk interface
- ❌ All ERP configuration

### Allowed Access (Read-Only)
- ✅ Sales Partner record (their own only)
- ✅ Commission Reports (filtered by User Permissions)
  - Sales Partner Commission Summary
  - Sales Partners Commission
  - Sales Partner Transaction Summary

### Data Isolation
- User Permissions ensure each partner ONLY sees their own data
- Applied to all doctypes automatically (`apply_to_all_doctypes = 1`)
- Cannot be bypassed - enforced at database level

## Troubleshooting

If you encounter errors:
1. Check that the site name is correct
2. Ensure you have Administrator access
3. Check Frappe logs for detailed error messages
4. Verify that Territory "All Territories" exists or can be created

