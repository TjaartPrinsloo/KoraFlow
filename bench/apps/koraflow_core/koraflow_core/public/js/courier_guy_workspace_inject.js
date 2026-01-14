/**
 * Courier Guy Workspace Script Injector
 * This script is loaded via workspace and injects the dashboard script
 */
(function() {
    'use strict';
    
    // Only run on Courier Guy workspace
    if (window.location.pathname.includes('courier-guy') || window.location.pathname.includes('courier_guy')) {
        // Load the dashboard script
        const script = document.createElement('script');
        script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
        script.async = true;
        document.head.appendChild(script);
        
        console.log('Courier Guy Dashboard: Script injector loaded, loading dashboard...');
    }
})();
