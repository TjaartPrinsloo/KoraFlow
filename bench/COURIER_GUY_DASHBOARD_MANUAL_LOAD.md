# Courier Guy Dashboard - Manual Loading Instructions

## Issue
The dashboard JavaScript is not loading automatically because Frappe hooks are not being discovered for the `koraflow_core` app.

## Quick Fix: Manual Script Injection

### Option 1: Browser Console (Recommended)
1. Navigate to: `http://localhost:8080/app/courier-guy`
2. Open browser console (F12)
3. Paste and run this script:

```javascript
(function() {
    if (window.courier_guy_dashboard_loaded) {
        console.log('✅ Dashboard already loaded');
        return;
    }
    const script = document.createElement('script');
    script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
    script.onload = function() {
        window.courier_guy_dashboard_loaded = true;
        console.log('✅ Courier Guy Dashboard loaded!');
        setTimeout(() => {
            if (window.koraflow_core?.courier_guy?.dashboard) {
                window.koraflow_core.courier_guy.dashboard.load_dashboard_data();
            }
        }, 1000);
    };
    document.head.appendChild(script);
})();
```

### Option 2: Browser Bookmarklet
Create a bookmark with this URL:
```javascript
javascript:(function(){if(!window.courier_guy_dashboard_loaded){const s=document.createElement('script');s.src='/assets/koraflow_core/js/courier_guy_dashboard.js?v='+Date.now();s.onload=function(){window.courier_guy_dashboard_loaded=true;console.log('✅ Dashboard loaded');};document.head.appendChild(s);}})();
```

Click the bookmark when on the Courier Guy workspace page.

## Permanent Fix: Fix Hooks Loading

The root issue is that Frappe is not discovering hooks from `koraflow_core`. To fix this:

1. **Check app installation:**
   ```bash
   cd /Users/tjaartprinsloo/Documents/KoraFlow/bench/sites
   python3 -c "import sys; sys.path.insert(0, '../apps'); import frappe; frappe.init('koraflow-site'); frappe.connect(); print('Installed apps:', frappe.get_installed_apps())"
   ```

2. **Reinstall the app (if needed):**
   ```bash
   cd /Users/tjaartprinsloo/Documents/KoraFlow/bench/sites
   python3 -m frappe.utils.bench_helper frappe --site koraflow-site reinstall --yes
   ```

3. **Or check hooks discovery:**
   The hooks file is correct, but Frappe may need to be restarted or the app may need to be reinstalled for hooks to be discovered.

## Files Created
- `/assets/koraflow_core/js/courier_guy_dashboard.js` - Main dashboard script
- `/assets/koraflow_core/js/courier_guy_workspace_hook.js` - Workspace hook (not loading due to hooks issue)
- `/assets/koraflow_core/js/global_courier_guy_inject.js` - Global injector (not loading due to hooks issue)

## Current Status
✅ Dashboard JavaScript code is complete and functional
✅ API endpoints are working
✅ Historical shipments integration is complete
❌ Hooks are not loading (Frappe not discovering koraflow_core hooks)
⚠️ Manual injection required until hooks issue is resolved
