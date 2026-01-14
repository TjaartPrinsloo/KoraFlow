# Signup Redirect to Intake Form - Fix Documentation

## Issue
After signup, users are not being redirected to the intake form (`/glp1-intake`).

## Root Cause
The signup process creates a user but doesn't automatically log them in, so when the redirect happens, the intake form page (which requires authentication) redirects them away or shows an error.

## Solution Implemented

### 1. Auto-Login Token System
- **File**: `bench/apps/koraflow_core/koraflow_core/api/auto_login.py`
- Created a new API endpoint `auto_login_with_token` that allows secure auto-login after signup
- Uses a temporary token stored in cache (expires in 5 minutes)
- Token contains user credentials for one-time use

### 2. Updated Signup Function
- **File**: `bench/apps/koraflow_core/koraflow_core/api/patient_signup.py`
- Modified `custom_sign_up()` to:
  - Generate a login token after user creation
  - Store token in cache with user credentials
  - Return token as 4th element in response tuple: `(status, message, redirect_url, login_token)`

### 3. Enhanced Frontend Redirect Handler
- **File**: `bench/apps/koraflow_core/koraflow_core/public/js/signup_redirect.js`
- Updated to:
  - Extract login token from signup response
  - Call `auto_login_with_token` API before redirecting
  - Redirect to intake form after successful auto-login
  - Fallback to direct redirect if auto-login fails

## How It Works

1. **User Signs Up**:
   - User fills out signup form
   - `custom_sign_up()` is called
   - User account is created with Patient role
   - Login token is generated and stored in cache
   - Response: `[3, "Account created...", "/glp1-intake", "token123..."]`

2. **Frontend Receives Response**:
   - `signup_redirect.js` intercepts the response
   - Detects status code 3 (success with redirect)
   - Extracts login token from response

3. **Auto-Login**:
   - Frontend calls `auto_login_with_token(token)`
   - Backend validates token and logs user in
   - Token is deleted after use

4. **Redirect**:
   - After successful login, redirect to `/glp1-intake`
   - User is now authenticated and can access the form

## Testing

### Manual Test Steps

1. **Clear browser cookies/session** (or use incognito)
2. Navigate to: `http://localhost:8000/login#signup`
3. Fill out signup form:
   - Full Name: Test User
   - Email: test@example.com
4. Click "Sign up"
5. **Expected**: Should automatically redirect to `/glp1-intake`

### Programmatic Test

```python
# Test the signup flow
from koraflow_core.api.patient_signup import custom_sign_up

result = custom_sign_up(
    email="test@example.com",
    full_name="Test User",
    redirect_to="/glp1-intake"
)

# Should return: (3, "Account created...", "/glp1-intake", "token...")
assert result[0] == 3
assert result[2] == "/glp1-intake"
assert len(result) >= 4  # Should have login token
```

## Troubleshooting

### Redirect Not Happening

1. **Check Browser Console**:
   - Open Developer Tools (F12)
   - Look for `[SignupRedirect]` log messages
   - Check for JavaScript errors

2. **Verify Token Generation**:
   ```python
   import frappe
   frappe.init(site='koraflow-site')
   frappe.connect()
   # Check if tokens are being created
   ```

3. **Check Auto-Login API**:
   - Test the endpoint directly:
   ```bash
   curl -X POST http://localhost:8000/api/method/koraflow_core.api.auto_login.auto_login_with_token \
     -d '{"token": "your_token_here"}'
   ```

### User Not Logged In After Redirect

1. **Check Session**:
   - After redirect, check if `frappe.session.user != "Guest"`
   - Verify cookies are set

2. **Token Expiration**:
   - Tokens expire after 5 minutes
   - If signup takes too long, token may expire

3. **Cache Issues**:
   - Clear Frappe cache: `bench --site [site] clear-cache`
   - Restart server if needed

## Security Considerations

- Login tokens expire after 5 minutes
- Tokens are single-use (deleted after login)
- Tokens are stored in cache (not database)
- Only valid for the specific user who signed up

## Alternative Approaches Considered

1. **Direct Backend Auto-Login**: 
   - Tried but had issues with session management in web request context
   - Current token-based approach is more reliable

2. **Email-Based Login**:
   - Could send login link via email
   - More secure but adds delay

3. **Temporary Session**:
   - Create temporary session for new signups
   - More complex to implement

## Files Modified

1. `bench/apps/koraflow_core/koraflow_core/api/patient_signup.py`
   - Added login token generation
   - Updated return value to include token

2. `bench/apps/koraflow_core/koraflow_core/api/auto_login.py` (NEW)
   - Auto-login API endpoint
   - Token validation and login

3. `bench/apps/koraflow_core/koraflow_core/public/js/signup_redirect.js`
   - Enhanced to handle login token
   - Auto-login before redirect

## Next Steps

1. Test the complete flow end-to-end
2. Monitor for any edge cases
3. Consider adding retry logic for failed auto-logins
4. Add user feedback if auto-login fails

