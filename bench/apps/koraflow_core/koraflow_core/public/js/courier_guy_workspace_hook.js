/**
 * Courier Guy Workspace Hook
 * Injects dashboard script when Courier Guy workspace is shown
 */
(function() {
    'use strict';
    
    // Wait for Frappe to be ready
    if (typeof frappe === 'undefined') {
        setTimeout(arguments.callee, 100);
        return;
    }
    
    // Hook into workspace show_page event
    if (frappe.views && frappe.views.Workspace) {
        const originalShowPage = frappe.views.Workspace.prototype.show_page;
        frappe.views.Workspace.prototype.show_page = function(page) {
            const result = originalShowPage.apply(this, arguments);
            
            // Check if this is the Courier Guy workspace
            if (page && (page.name === 'Courier Guy' || page.title === 'Courier Guy' || 
                (page.content && page.content.includes('Courier Guy Dashboard')))) {
                
                // Load dashboard script if not already loaded
                if (!window.courier_guy_dashboard_loaded) {
                    setTimeout(() => {
                        const script = document.createElement('script');
                        script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
                        script.onload = function() {
                            window.courier_guy_dashboard_loaded = true;
                            console.log('Courier Guy Dashboard: Script loaded via workspace hook');
                        };
                        script.onerror = function() {
                            console.error('Courier Guy Dashboard: Failed to load script');
                        };
                        document.head.appendChild(script);
                    }, 500);
                }
            }
            
            return result;
        };
    }
    
    // Also check on route change
    if (frappe.router) {
        frappe.router.on('change', function() {
            const route = frappe.get_route();
            if (route && route.length >= 2 && route[0] === 'workspace' && 
                (route[1] === 'Courier Guy' || route[1] === 'courier-guy' || route[1] === 'courier_guy')) {
                
                if (!window.courier_guy_dashboard_loaded) {
                    setTimeout(() => {
                        const script = document.createElement('script');
                        script.src = '/assets/koraflow_core/js/courier_guy_dashboard.js?v=' + Date.now();
                        script.onload = function() {
                            window.courier_guy_dashboard_loaded = true;
                            console.log('Courier Guy Dashboard: Script loaded via route hook');
                        };
                        document.head.appendChild(script);
                    }, 1000);
                }
            }
        });
    }
})();
