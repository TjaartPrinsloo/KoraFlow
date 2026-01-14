# KoraFlow Workspace Permissions - Testing Checklist

## ✅ Setup Verification

### 1. DocType Permissions (Server-Side)
- [x] **Employee role**: `create=0, write=0, read=1` ✓
- [x] **Physician role**: `create=0, write=0, read=1` ✓
- [x] **Desk User role**: `create=1, write=1, read=1` (normal users)
- [x] **Workspace Manager role**: `create=1, write=1, read=1` (admins)

### 2. Backend Override
- [x] Hook configured: `frappe.desk.desktop.get_workspace_sidebar_items` → `koraflow_core.utils.workspace_override.get_workspace_sidebar_items`
- [x] Server-side logic ensures:
  - Administrators see all workspaces including hidden HR/Payroll children
  - Employees have `has_create_access = False`
  - Sales Partners only see Sales Partner Dashboard
  - Healthcare workspace content filtered for Employees

### 3. Client-Side Files
- [x] **JavaScript**: Minimal (28 lines) - only adds body classes
- [x] **CSS**: Clean, role-based UI hiding rules
- [x] Files copied to `/assets/koraflow_core/` directory

---

## 🧪 Testing Steps

### Test 1: Administrator Role
**User**: Administrator or System Manager

1. **Hard refresh browser** (Cmd+Shift+R / Ctrl+Shift+R)
2. **Check browser console**:
   - Should see: `[KoraFlow] hide_help_and_settings.js loaded`
   - No 404 errors for JS/CSS files
   - Body should have class: `is-admin`

3. **Verify HR Workspace**:
   - HR workspace should be visible in sidebar
   - Drop-down icon should be visible
   - Click to expand - all child workspaces should be visible
   - Hidden child workspaces (if any) should be visible

4. **Verify Payroll Workspace**:
   - Payroll workspace should be visible in sidebar
   - Drop-down icon should be visible
   - Click to expand - all child workspaces should be visible
   - Hidden child workspaces (if any) should be visible

5. **Verify Workspace Creation**:
   - "New Workspace" button should be visible
   - Should be able to create new workspaces

**Expected Result**: ✅ All workspaces visible, including hidden HR/Payroll children

---

### Test 2: Employee Role
**User**: User with Employee role (not Administrator)

1. **Hard refresh browser** (Cmd+Shift+R / Ctrl+Shift+R)
2. **Check browser console**:
   - Should see: `[KoraFlow] hide_help_and_settings.js loaded`
   - Body should have class: `is-employee`

3. **Verify UI Restrictions**:
   - Help button should be hidden
   - "New Workspace" button should be hidden
   - Sidebar section labels (PUBLIC, Personal) should be hidden

4. **Verify Workspace Creation (API Test)**:
   - Open browser DevTools → Network tab
   - Try to create workspace via UI (if button somehow appears)
   - OR test via console:
     ```javascript
     frappe.call({
       method: 'frappe.desk.doctype.workspace.workspace.new_page',
       args: { new_page: JSON.stringify({ title: 'Test', public: 0 }) }
     }).then(r => console.log('Result:', r)).catch(e => console.log('Error:', e));
     ```
   - Should receive permission error

5. **Verify Healthcare Workspace**:
   - Healthcare workspace should be visible
   - Content should be filtered (only allowed shortcuts visible)
   - Reports & Masters section should be hidden

**Expected Result**: ✅ No create access, UI elements hidden, API rejects creation

---

### Test 3: Physician Role
**User**: User with Physician role (not Administrator)

1. **Hard refresh browser** (Cmd+Shift+R / Ctrl+Shift+R)
2. **Follow same steps as Employee role**
3. **Verify same restrictions apply**

**Expected Result**: ✅ Same as Employee - no create access

---

### Test 4: Sales Partner Portal Role
**User**: User with Sales Partner Portal role

1. **Hard refresh browser** (Cmd+Shift+R / Ctrl+Shift+R)
2. **Check browser console**:
   - Body should have class: `is-sales-partner`

3. **Verify Workspace Filtering**:
   - Only "Sales Partner Dashboard" workspace should be visible
   - All other workspaces should be hidden

4. **Verify Menu Restrictions**:
   - User dropdown menu should not show:
     - Apps
     - View Website
     - Session Defaults
     - My Settings

5. **Verify Workspace Creation**:
   - "New Workspace" button should be hidden
   - API should reject workspace creation

**Expected Result**: ✅ Only Sales Partner Dashboard visible, menu items restricted

---

## 🔍 Troubleshooting

### Issue: HR/Payroll submenu items not showing for Administrator

**Check**:
1. Browser console for JavaScript errors
2. Network tab - verify `get_workspace_sidebar_items` API call returns HR/Payroll children
3. Server logs for workspace_override.py execution
4. Verify `is-admin` class is on body element
5. Check CSS rules are loading (inspect element, check computed styles)

**Fix**:
- Verify backend override is working (check API response)
- Verify CSS rules are applied
- Hard refresh browser cache

---

### Issue: Employee can still create workspaces

**Check**:
1. User's roles - might have Desk User role with create permission
2. Backend override sets `has_create_access = False` (check API response)
3. DocType permissions are correct (Employee: create=0)

**Fix**:
- Backend override should prevent creation even if user has Desk User role
- API will reject creation attempts
- UI button is hidden via CSS

---

### Issue: Files returning 404

**Check**:
1. Files exist in `sites/assets/koraflow_core/js/` and `sites/assets/koraflow_core/css/`
2. Hooks.py has correct paths: `/assets/koraflow_core/js/...`
3. Server has been restarted

**Fix**:
- Copy files to assets directory
- Restart server
- Hard refresh browser

---

## 📊 Architecture Summary

```
┌─────────────────────────────────────┐
│  Server-Side Enforcement            │
│  - DocType Permissions              │
│  - workspace_override.py            │
│  ✅ Decides what exists             │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Client-Side Reflection              │
│  - CSS (koraflow_core.css)          │
│  - JS (hide_help_and_settings.js)   │
│  ✅ Reflects server state           │
└─────────────────────────────────────┘
```

**Key Principle**: Server decides, client reflects. No client-side permission enforcement.

---

## ✅ Success Criteria

- [ ] Administrators see all workspaces including hidden HR/Payroll children
- [ ] Employees cannot create workspaces (UI hidden + API rejects)
- [ ] Physicians cannot create workspaces (UI hidden + API rejects)
- [ ] Sales Partners only see Sales Partner Dashboard
- [ ] No JavaScript errors in console
- [ ] No 404 errors for assets
- [ ] Performance is good (no layout thrashing, no setTimeout storms)

---

**Last Updated**: After refactoring to server-side architecture
**Status**: Ready for testing

