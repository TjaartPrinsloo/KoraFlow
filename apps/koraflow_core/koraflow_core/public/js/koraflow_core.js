/**
 * KoraFlow Core JavaScript
 * Frontend branding and module management
 */

frappe.provide('koraflow');

// Branding map
koraflow.branding = {
	'Frappe': 'KoraFlow Core',
	'ERPNext': 'KoraFlow ERP',
	'ERPNext Healthcare': 'KoraFlow Healthcare',
	'ERPNext HR': 'KoraFlow Workforce',
	'ERPNext CRM': 'KoraFlow CRM',
	'ERPNext Helpdesk': 'KoraFlow Support',
	'ERPNext Insights': 'KoraFlow Insights',
};

// Apply branding to text
koraflow.applyBranding = function(text) {
	if (!text) return text;
	
	let branded = text;
	for (const [original, branded_name] of Object.entries(koraflow.branding)) {
		branded = branded.replace(new RegExp(original, 'g'), branded_name);
	}
	return branded;
};

// Apply branding on page load
frappe.ready(function() {
	// Apply branding to page title
	if (document.title) {
		document.title = koraflow.applyBranding(document.title);
	}
	
	// Apply branding to workspace labels
	frappe.call({
		method: 'koraflow_core.koraflow_core.branding.get_branding_info',
		callback: function(r) {
			if (r.message) {
				// Update branding map with server-side values
				if (r.message.branding_map) {
					Object.assign(koraflow.branding, r.message.branding_map);
				}
			}
		}
	});
});

// Module management
koraflow.modules = {
	toggle: function(module_name, enable, callback) {
		frappe.call({
			method: 'koraflow_core.koraflow_core.module_registry.toggle_module',
			args: {
				module_name: module_name,
				enable: enable
			},
			callback: function(r) {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({
						message: __(enable ? 'Module enabled' : 'Module disabled'),
						indicator: 'green'
					});
					if (callback) callback(r.message);
				}
			}
		});
	},
	
	getStatus: function(callback) {
		frappe.call({
			method: 'koraflow_core.koraflow_core.module_registry.get_all_modules_status',
			callback: function(r) {
				if (callback) callback(r.message);
			}
		});
	}
};

