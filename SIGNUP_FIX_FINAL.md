# Signup Fix - Final Implementation

## Problem
The signup was failing with error: `Could not find User Type: Website User`

## Root Cause
Frappe's default `sign_up` function hardcodes `user_type: "Website User"`, which doesn't exist in this ERPNext installation.

## Solutions Applied

### 1. Frontend Fixes
- **`signup_form.js`**: Updated to call `koraflow_core.api.patient_signup.patient_sign_up` directly instead of the default Frappe signup
- **`signup_redirect.js`**: Updated to intercept and redirect signup calls to the custom passwordless signup function

### 2. Backend Fixes
- **Frappe `user.py`**: Patched to use dynamic user type detection instead of hardcoded "Website User"
  - Location: `bench/apps/frappe/frappe/core/doctype/user/user.py` (line ~1004)
  - Change: Uses `frappe.db.get_value("User", {"user_type": ["!=", ""]}, "user_type") or "System User"` instead of `"Website User"`

### 3. Module Override
- **`user_override.py`**: Attempts to override Frappe's signup at module load time
- **`__init__.py`**: Imports and applies the override when the module loads

## Required Actions

### Server Restart Required
The Frappe `user.py` patch requires a server restart to take effect. The frontend changes should work immediately after a hard browser refresh (Ctrl+Shift+R or Cmd+Shift+R).

### Testing Steps
1. **Hard refresh the browser** (Ctrl+Shift+R / Cmd+Shift+R) to clear cached JavaScript
2. Navigate to `/login#signup`
3. Fill in Full Name and Email (no password field should appear)
4. Click "Sign up"
5. Should show "Please check your email for verification" message
6. After email verification and password setup, should redirect to `/glp1-intake-wizard`

## Files Modified
- `bench/apps/koraflow_core/koraflow_core/public/js/signup_form.js`
- `bench/apps/koraflow_core/koraflow_core/public/js/signup_redirect.js`
- `bench/apps/frappe/frappe/core/doctype/user/user.py`
- `bench/apps/koraflow_core/koraflow_core/doctype/user/user_override.py`
- `bench/apps/koraflow_core/koraflow_core/__init__.py`

## Note
If the error persists after server restart, the frontend JavaScript changes should still work as they bypass the default Frappe signup entirely and call the custom passwordless signup function directly.
