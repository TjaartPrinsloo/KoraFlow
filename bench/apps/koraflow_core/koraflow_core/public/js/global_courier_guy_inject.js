/**
 * Global Courier Guy Dashboard Injector
 * This script should be loaded globally and will inject the dashboard when needed
 */
(function() {
    'use strict';
    
    function injectDashboard() {
        if (window.courier_guy_dashboard_loaded) return;
        
        const pathname = window.location.pathname.toLowerCase();
        const route = (typeof frappe !== 'undefined' && frappe.get_route) ? frappe.get_route() : [];
        
        const isCourierGuyPage = 
            pathname.includes('courier-guy') || 
            pathname.includes('courier_guy') ||
            (route && route.length >= 2 && route[0] === 'workspace' && 
             (route[1] === 'Courier Guy' || route[1] === 'courier-guy' || route[1] === 'courier_guy'));
        
        if (isCourierGuyPage) {
            const script = document.createElement('script');
            script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
            script.onload = function() {
                window.courier_guy_dashboard_loaded = true;
                console.log('✅ Courier Guy Dashboard: Script loaded via global injector');
            };
            script.onerror = function() {
                console.error('❌ Courier Guy Dashboard: Failed to load script');
            };
            document.head.appendChild(script);
        }
    }
    
    // Try multiple initialization methods
    if (typeof frappe !== 'undefined' && typeof frappe.ready === 'function') {
        frappe.ready(injectDashboard);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectDashboard);
    } else {
        injectDashboard();
    }
    
    // Also check periodically
    setInterval(injectDashboard, 2000);
    
    // Hook into workspace if available
    if (typeof frappe !== 'undefined' && frappe.router && frappe.router.on) {
        frappe.router.on('change', function() {
            setTimeout(injectDashboard, 500);
        });
    }
})();
