// Courier Guy Workspace Page Script
// This script loads when the Courier Guy workspace is viewed

frappe.ready(function() {
    // Load the dashboard script
    if (!window.courier_guy_dashboard_loaded) {
        const script = document.createElement('script');
        script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
        script.onload = function() {
            window.courier_guy_dashboard_loaded = true;
            console.log('Courier Guy Dashboard: Script loaded via page script');
        };
        script.onerror = function() {
            console.error('Courier Guy Dashboard: Failed to load script');
        };
        document.head.appendChild(script);
    }
});
