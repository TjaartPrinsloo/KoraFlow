# Notification Settings Permission Fix

## Problem
"User Guest does not have doctype access via role permission for document Notification Settings"

This error occurs when Guest tries to access Notification Settings, which is created automatically during User creation.

## Root Cause

Frappe's `User.after_insert()` method calls `create_notification_settings(self.name)`. This happens automatically when `user.insert()` is called, and it runs in the context of whoever called `insert()`, not necessarily Administrator.

## All Notification Settings Access Points

### 1. ✅ User Creation (`patient_sign_up`)
**Location**: `koraflow_core/api/patient_signup.py:785-824`

**Fix Applied**:
- Override `User.after_insert()` to run with Administrator context
- Wrap entire user creation in `frappe.as_user("Administrator")`
- Ensure `user.insert()` triggers `after_insert()` with Administrator permissions

**Code**:
```python
# Override after_insert to ensure Administrator context
from frappe.core.doctype.user.user import User as FrappeUser
original_after_insert = FrappeUser.after_insert

def safe_after_insert(self):
    original_user = frappe.session.user
    try:
        frappe.set_user("Administrator")
        frappe.flags.ignore_permissions = True
        original_after_insert(self)  # Creates Notification Settings
    finally:
        frappe.flags.ignore_permissions = False
        frappe.set_user(original_user)

FrappeUser.after_insert = safe_after_insert

try:
    with frappe.as_user("Administrator"):
        user.insert()  # Triggers after_insert with Administrator context
finally:
    FrappeUser.after_insert = original_after_insert  # Restore
```

### 2. ✅ Email Sending (`send_verification_email`)
**Location**: `koraflow_core/api/patient_signup.py:942-970`

**Fix Applied**:
- Called within `frappe.as_user("Administrator")` context from `patient_sign_up()`
- `frappe.sendmail()` doesn't directly access Notification Settings, but called safely

### 3. ✅ Password Reset (`verify_email` and `force_verify_email`)
**Location**: `koraflow_core/api/patient_signup.py:912-950` and `975-1000`

**Fix Applied**:
- Wrapped `user.reset_password(send_email=True)` in `frappe.as_user("Administrator")`
- `reset_password()` internally may access Notification Settings

### 4. ✅ User Document Access (`verify_email`)
**Location**: `koraflow_core/api/patient_signup.py:873-925`

**Fix Applied**:
- Use `frappe.db.get()` and `frappe.db.sql()` for read-only operations (Guest OK)
- Only call `frappe.get_doc("User", ...)` within Administrator context when needed

## Verification Checklist

Run this to verify all operations use Administrator context:

```python
# In Frappe console
import frappe
from koraflow_core.api.patient_signup import patient_sign_up

# Test signup
frappe.set_user("Guest")
status, msg = patient_sign_up("test@example.com", "Test User")
# Should NOT raise Notification Settings error
```

## Testing

1. **Test User Creation**:
   ```bash
   bench --site [site] console
   ```
   ```python
   exec(open('apps/koraflow_core/test_signup_flow.py').read())
   ```

2. **Check Error Logs**:
   ```bash
   bench --site [site] console
   ```
   ```python
   frappe.get_all("Error Log", filters={"error": ["like", "%Notification Settings%"]}, limit=10)
   ```

## Key Points

1. ✅ **User.insert()** - Override `after_insert()` to use Administrator context
2. ✅ **frappe.sendmail()** - Called within Administrator context
3. ✅ **reset_password()** - Called within Administrator context  
4. ✅ **frappe.get_doc("User")** - Only called within Administrator context when writing
5. ✅ **Read operations** - Use `frappe.db.get()` or `frappe.db.sql()` (Guest OK)

## Files Modified

- `koraflow_core/api/patient_signup.py` - All user creation/email/password operations
- `koraflow_core/doctype/user/user.py` - Updated hook to be safer

## If Error Persists

1. Check error log for exact line number
2. Verify `frappe.as_user("Administrator")` context is active
3. Ensure `after_insert` override is applied before `user.insert()`
4. Check if custom hooks are interfering

