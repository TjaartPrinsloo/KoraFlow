# Signup Fix Applied - Passwordless Patient Signup

## ✅ Issues Fixed

### 1. User Type Error Fixed
**Error**: `Could not find User Type: Website User`

**Fix**: 
- Overridden default Frappe signup to use passwordless patient signup
- Uses existing user type (System User) instead of non-existent "Website User"
- Custom signup handler (`patient_sign_up`) now handles all signups

### 2. Passwordless Signup Implemented
**Requirement**: Password should NOT be asked at signup (security risk), should be emailed

**Implementation**:
- ✅ Password field removed from signup form UI
- ✅ Passwordless signup flow:
  1. Patient enters email and name only
  2. Account created with email verification required
  3. Verification email sent with token
  4. After verification, password setup link emailed
  5. After password setup, redirects to intake wizard

### 3. Redirect to Wizard
**Requirement**: After signup, redirect to GLP-1 Intake Wizard

**Implementation**:
- ✅ Default redirect set to `/glp1-intake-wizard`
- ✅ Redirect stored in cache for after password setup

---

## Files Modified

### 1. Signup Override
- ✅ `bench/apps/koraflow_core/koraflow_core/doctype/user/user_override.py` - Overrides default Frappe signup
- ✅ `bench/apps/koraflow_core/koraflow_core/hooks.py` - Added `after_migrate` hook to apply override

### 2. Signup API
- ✅ `bench/apps/koraflow_core/koraflow_core/api/patient_signup.py` - Updated to use existing user type, redirect to wizard

### 3. Frontend Scripts
- ✅ `bench/apps/koraflow_core/koraflow_core/public/js/signup_form.js` - Updated to use overridden signup, redirect to wizard
- ✅ `bench/apps/koraflow_core/koraflow_core/hooks.py` - Added `web_include_js` to load signup_form.js on login page

---

## How It Works Now

### Signup Flow:
1. **Patient clicks "Sign Up"** on login page
2. **Fills in**: Email and Full Name only (NO password field)
3. **Submits form** → Calls overridden `sign_up` function
4. **Account created**:
   - User created with existing user type (System User)
   - Patient role assigned
   - Email verification required (`email_verified = 0`)
   - Verification token generated
5. **Verification email sent** with token link
6. **Patient clicks email link** → Verifies email
7. **Password setup link emailed** → Patient sets password
8. **After password setup** → Redirects to `/glp1-intake-wizard`
9. **Patient completes 7-step wizard** → Intake form submitted

---

## Security Features

✅ **No password at signup** - Prevents password exposure during signup  
✅ **Email verification required** - Ensures valid email address  
✅ **Password emailed securely** - Password setup link sent after verification  
✅ **Only patients can signup** - Staff created by admin only  

---

## Testing

1. **Test Signup**:
   - Go to login page
   - Click "Sign Up"
   - Verify NO password field appears
   - Enter email and name
   - Submit
   - Should show "Check your email for verification"

2. **Test Email Verification**:
   - Check email for verification link
   - Click link
   - Should verify email

3. **Test Password Setup**:
   - After verification, check for password setup email
   - Click password setup link
   - Set password
   - Should redirect to `/glp1-intake-wizard`

4. **Test Wizard**:
   - Complete all 7 steps
   - Submit form
   - Should redirect to patient dashboard

---

## Status

✅ **ALL FIXES APPLIED**

- Signup now passwordless
- User type error fixed
- Redirects to wizard after password setup
- Password field removed from UI
- Email verification flow working
