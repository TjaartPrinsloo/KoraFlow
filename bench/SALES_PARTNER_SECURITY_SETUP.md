# Sales Partner Security Setup - Complete ✅

## Overview

All 46 sales partners have been configured with **secure, compliant permissions** that ensure:
- ✅ They can ONLY see their own commission data
- ❌ They CANNOT see patients, invoices, prescriptions, stock, or access Desk
- 🔒 Data isolation is enforced at the database level via User Permissions

## What Was Done

### 1. Created Sales Partner Portal Role ✅
- **Role Name:** `Sales Partner Portal`
- **Desk Access:** Disabled (Portal users only)
- **Purpose:** Single-purpose role for commission-only access

### 1b. Created Module Profile ✅
- **Module Profile Name:** `Sales Partner Module Profile`
- **Blocks:** Drive module
- **Purpose:** Prevents Drive app from appearing in portal menu
- **Assigned to:** All 46 sales partner users

### 2. Blocked Access to Sensitive DocTypes ✅
Blocked 47 sensitive doctypes including:
- **Healthcare:** Patient, Patient Encounter, Medication, Prescription, Lab Test, etc.
- **Financial:** Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry, etc.
- **Inventory:** Item, Stock Entry, Warehouse, Bin, etc.
- **Sales/Purchase:** Sales Order, Purchase Order, Quotation, etc.
- **System:** Company, User, Role, Workspace, etc.

### 3. Granted Read-Only Access to Commission Data ✅
- **DocType:** Sales Partner (their own record only)
- **Reports:**
  - Sales Partner Commission Summary
  - Sales Partners Commission
  - Sales Partner Transaction Summary

### 4. Updated All Users ✅
- **User Type:** Changed from `System User` → `Website User` (Portal User)
- **Role:** Changed from `Sales User` → `Sales Partner Portal`
- **Total Updated:** 46 users

### 5. Set Up User Permissions ✅
- **Created:** 46 User Permissions
- **Configuration:** `apply_to_all_doctypes = 1`
- **Effect:** Each partner can ONLY see records where `sales_partner = themselves`

## Security Architecture

```
Sales Partner User
├── User Type: Website User (Portal, NOT Desk)
├── Role: Sales Partner Portal
├── User Permission: Sales Partner = [Their Own Name]
│   └── Apply To All DocTypes: ✅
│
├── ✅ CAN ACCESS:
│   ├── Sales Partner (their own record)
│   └── Commission Reports (filtered by User Permission)
│
└── ❌ CANNOT ACCESS:
    ├── Patient records
    ├── Invoices
    ├── Prescriptions
    ├── Stock/Inventory
    ├── Desk interface
    └── All ERP configuration
```

## Data Isolation

**User Permissions** ensure that:
1. Each sales partner user has a User Permission linking them to their Sales Partner record
2. This permission applies to ALL doctypes (`apply_to_all_doctypes = 1`)
3. Frappe automatically filters all queries to only show records where `sales_partner = their own`
4. This is enforced at the **database query level** - cannot be bypassed

## Compliance

This setup is **compliant with Schedule 4 medication regulations** because:
- Sales partners have **zero access** to patient data
- Sales partners have **zero access** to prescription data
- Sales partners have **zero access** to medication data
- All access is **read-only** for commission data only
- Data isolation is **enforced at database level**

## Files Created

1. **`create_sales_partners.py`** - Creates sales partners and users (updated for security)
2. **`setup_sales_partner_permissions.py`** - Sets up role and permissions
3. **`update_existing_sales_partners.py`** - Updates existing users
4. **`add_user_permissions_to_sales_partners.py`** - Adds User Permissions

## Verification

To verify the setup:

1. **Check User Type:**
   ```python
   frappe.db.get_value("User", "adri.kotze@koraflow.com", "user_type")
   # Should return: "Website User"
   ```

2. **Check Role:**
   ```python
   frappe.get_roles("adri.kotze@koraflow.com")
   # Should include: "Sales Partner Portal"
   # Should NOT include: "Sales User"
   ```

3. **Check User Permission:**
   ```python
   frappe.get_all("User Permission", 
       filters={"user": "adri.kotze@koraflow.com", "allow": "Sales Partner"})
   # Should return permission with for_value = "Adri Kotze"
   ```

4. **Test Access:**
   - Login as a sales partner user
   - Should NOT see Desk
   - Should NOT see Patient list
   - Should NOT see Invoice list
   - Should see Portal with commission reports (filtered to their own data only)

## Important Notes

⚠️ **CRITICAL:**
- Sales partners are **Portal Users** - they access via website portal, NOT Desk
- User Permissions are **mandatory** - without them, partners could see all data
- Role permissions are **restrictive** - blocked by default, only commission data allowed
- This setup is **non-negotiable** for compliance

✅ **SAFE:**
- All access is read-only
- Data isolation is automatic via User Permissions
- Cannot bypass restrictions (enforced at database level)
- Compliant with medical data regulations

## Maintenance

If you need to add new sales partners:

1. Run `create_sales_partners.py` - it will automatically:
   - Create as Website User
   - Assign Sales Partner Portal role
   - Create User Permission

2. The permissions are already set up, so new users will automatically have:
   - Correct user type
   - Correct role
   - User Permissions for data isolation

## Support

If you encounter issues:
1. Check that `setup_sales_partner_permissions.py` has been run
2. Verify User Permissions exist for each user
3. Check that users have `Sales Partner Portal` role (not `Sales User`)
4. Verify user_type is `Website User` (not `System User`)

