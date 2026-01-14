/**
 * Manual Injection Script for Courier Guy Dashboard
 * 
 * Copy and paste this entire script into your browser console (F12) 
 * when you're on the Courier Guy workspace page.
 * 
 * Or add it as a bookmarklet for one-click loading.
 */

(function() {
    'use strict';
    
    // Check if already loaded
    if (window.courier_guy_dashboard_loaded) {
        console.log('✅ Courier Guy Dashboard already loaded');
        return;
    }
    
    console.log('🔄 Loading Courier Guy Dashboard...');
    
    // Load the dashboard script
    const script = document.createElement('script');
    script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
    
    script.onload = function() {
        window.courier_guy_dashboard_loaded = true;
        console.log('✅ Courier Guy Dashboard script loaded!');
        
        // Wait a bit for initialization, then trigger dashboard
        setTimeout(function() {
            if (window.koraflow_core && 
                window.koraflow_core.courier_guy && 
                window.koraflow_core.courier_guy.dashboard) {
                console.log('✅ Initializing dashboard...');
                window.koraflow_core.courier_guy.dashboard.load_dashboard_data();
            } else {
                console.log('⚠️ Dashboard object not ready yet, will auto-load when ready');
            }
        }, 1000);
    };
    
    script.onerror = function() {
        console.error('❌ Failed to load Courier Guy Dashboard script');
        console.error('Please check that the file exists at: /assets/koraflow_core/js/courier_guy_dashboard.js');
    };
    
    document.head.appendChild(script);
})();
