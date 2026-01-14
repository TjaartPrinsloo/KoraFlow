# Courier Guy Dashboard - Debugging Guide

## Issue: Dashboard Not Appearing

The dashboard should appear at the top of the Courier Guy workspace. If it's not showing, follow these steps:

## Step 1: Check Browser Console

1. Open Courier Guy workspace
2. Press `F12` to open Developer Tools
3. Go to **Console** tab
4. Look for messages starting with "Courier Guy Dashboard"
5. Check for any JavaScript errors (red text)

## Step 2: Verify Script is Loaded

In the browser console, run:

```javascript
// Check if the script is loaded
console.log('koraflow_core available:', typeof koraflow_core !== 'undefined');
console.log('courier_guy available:', typeof koraflow_core !== 'undefined' && koraflow_core.courier_guy);
console.log('dashboard available:', typeof koraflow_core !== 'undefined' && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard);
```

**Expected**: All should return `true`

## Step 3: Manually Trigger Dashboard

If the script is loaded but dashboard isn't showing, manually trigger it:

```javascript
if (koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) {
    koraflow_core.courier_guy.dashboard.load_dashboard_data();
}
```

## Step 4: Check Network Tab

1. Open **Network** tab in Developer Tools
2. Refresh the page
3. Look for `courier_guy_dashboard.js` in the list
4. Check if it loaded successfully (status 200)

## Step 5: Rebuild Assets (if needed)

If the JavaScript file isn't loading, rebuild assets:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
source env/bin/activate
bench build
```

Or if `bench` command isn't available:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
source env/bin/activate
python -m frappe build
```

## Step 6: Alternative - Direct Injection Test

If the automatic injection isn't working, you can manually inject the dashboard:

```javascript
// Find the container
const container = document.querySelector('.col.layout-main-section-wrapper') || 
                  document.querySelector('.layout-main-section-wrapper');

if (container) {
    // Create dashboard HTML
    const dashboardHTML = `
        <div class="courier-guy-api-dashboard" style="margin: 20px 0; padding: 20px; background: #fff; border-radius: 8px;">
            <div class="dashboard-header">
                <h4>Courier Guy Live Dashboard</h4>
                <button class="btn btn-sm btn-secondary" onclick="location.reload()">
                    <i class="fa fa-refresh"></i> Refresh
                </button>
            </div>
            <div class="dashboard-loading">
                <i class="fa fa-spinner fa-spin"></i> Loading dashboard data...
            </div>
        </div>
    `;
    
    // Insert at top
    container.insertAdjacentHTML('afterbegin', dashboardHTML);
    
    // Then load data
    if (koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) {
        koraflow_core.courier_guy.dashboard.fetch_dashboard_data();
    }
}
```

## Common Issues

### Issue: Script not loading
**Solution**: Rebuild assets with `bench build` or clear cache and hard refresh

### Issue: Container not found
**Solution**: The workspace might not be fully loaded. Wait a few seconds and try again, or use the manual injection code above.

### Issue: JavaScript errors
**Solution**: Check the console for specific errors and fix them. Common issues:
- Missing dependencies
- Syntax errors
- Timing issues

## Files to Check

1. **JavaScript**: `bench/apps/koraflow_core/koraflow_core/public/js/courier_guy_dashboard.js`
2. **CSS**: `bench/apps/koraflow_core/koraflow_core/public/css/courier_guy_dashboard.css`
3. **Hooks**: `bench/apps/koraflow_core/koraflow_core/hooks.py` (should include both files)

## Quick Fix

If nothing works, you can add the dashboard directly to the workspace content JSON by editing:
`bench/apps/koraflow_core/koraflow_core/workspace/courier_guy/courier_guy.json`

And adding a custom block or HTML content at the beginning of the content array.

