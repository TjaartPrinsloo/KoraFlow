/**
 * Manual injection script for Courier Guy Dashboard
 * This will be loaded directly in the workspace
 */
(function() {
    'use strict';
    
    // Wait for page to load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Check if we're on courier-guy page
        const pathname = window.location.pathname.toLowerCase();
        if (!pathname.includes('courier-guy') && !pathname.includes('courier_guy')) {
            return;
        }
        
        // Load the dashboard script
        const script = document.createElement('script');
        script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
        script.onload = function() {
            console.log('Courier Guy Dashboard: Script loaded manually');
        };
        script.onerror = function() {
            console.error('Courier Guy Dashboard: Failed to load script');
        };
        document.head.appendChild(script);
    }
})();
