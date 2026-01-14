# Testing Signup → Verification → Intake Flow

## Prerequisites

1. Run the patch to add custom fields:
   ```bash
   bench --site [site-name] migrate
   ```

2. Ensure email is configured (or check console logs for email links in development)

3. Clear browser cache or use incognito mode

## Test Flow

### Step 1: Patient Signup (No Password)

1. Navigate to: `http://localhost:8000/login#signup`
2. Fill in:
   - Email: `test.patient@example.com`
   - Full Name: `Test Patient`
3. **Verify**: No password field is visible
4. Click "Sign Up"
5. **Expected**: Success message "Please check your email to verify your account"

### Step 2: Email Verification

1. Check email inbox (or console logs in development mode)
2. Click verification link: `/verify-email?token=[token]&email=test.patient@example.com`
3. **Expected**: 
   - Page shows "Email Verified!"
   - Message: "Your email has been verified! Please check your email for password setup instructions."
   - Password setup email is sent

### Step 3: Password Setup

1. Check email for password reset link
2. Click link (goes to `/update-password?key=[key]`)
3. Set new password
4. Click "Confirm"
5. **Expected**: 
   - Password is set successfully
   - Auto-redirect to `/glp1-intake`

### Step 4: Intake Form Completion

1. Should be redirected to `/glp1-intake` after password setup
2. Fill out intake form
3. Submit form
4. **Expected**:
   - Form submits successfully
   - `intake_completed` flag set to 1 in User doctype
   - User can now access portal pages

### Step 5: Portal Access Verification

1. Try accessing portal pages (e.g., `/app/patient`)
2. **Expected**: 
   - Before intake: Redirected to `/glp1-intake`
   - After intake: Can access portal pages

## Admin Force Verify Test

1. Login as Administrator
2. Navigate to User form for unverified user
3. **Verify**: "Force Verify Email" button is visible
4. Click button
5. Enter reason (optional): "Assisted signup - patient cannot access email"
6. Click "Verify"
7. **Expected**:
   - Email verified
   - Password setup email sent
   - Fields updated: `email_verified_via = "Admin"`, `email_verified_by = [admin user]`

## Verification Checklist

- [ ] Signup form has NO password field
- [ ] User created with `email_verified = 0`
- [ ] Verification email sent with token
- [ ] Email verification link works
- [ ] Password setup email sent after verification
- [ ] Password setup redirects to `/glp1-intake`
- [ ] Intake form accessible after password setup
- [ ] Portal access blocked until intake completed
- [ ] `intake_completed = 1` after form submission
- [ ] Admin force verify button works
- [ ] All operations use Administrator context (no Notification Settings errors)

## Common Issues

### "Notification Settings" Error
- **Cause**: Operations running as Guest
- **Fix**: Ensure all user creation/email/password reset uses `frappe.as_user("Administrator")`

### Verification Link Not Working
- **Check**: Token is correctly hashed and stored
- **Check**: Email contains correct verification URL

### Password Setup Email Not Sent
- **Check**: Email server is configured
- **Check**: `reset_password()` is called within Administrator context

### Intake Form Not Accessible
- **Check**: User is logged in
- **Check**: `email_verified = 1`
- **Check**: Intake enforcement middleware is not blocking incorrectly

