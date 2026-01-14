// Wait for frappe to be available
(function() {
	if (typeof frappe !== 'undefined' && typeof frappe.ready === 'function') {
		frappe.ready(function() {
			// Check intake form status on page load
			check_intake_form_status();
			
			// Also check after login
			$(document).on('login', function() {
				check_intake_form_status();
			});
		});
	} else {
		// Fallback if frappe.ready is not available
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', function() {
				setTimeout(check_intake_form_status, 1000);
			});
		} else {
			setTimeout(check_intake_form_status, 1000);
		}
	}
})();

function check_intake_form_status() {
	// Check if frappe is available
	if (typeof frappe === 'undefined' || !frappe.session || !frappe.call) {
		// Wait a bit and try again
		setTimeout(check_intake_form_status, 500);
		return;
	}
	
	// Only check if user is logged in and not on intake form page
	if (frappe.session.user === 'Guest') {
		return;
	}
	
	// Don't redirect if already on intake form page
	if (window.location.pathname.includes('glp1-intake') || 
		window.location.pathname.includes('intake-form')) {
		return;
	}
	
	// Don't redirect on list views or other system pages
	if (window.location.pathname.includes('/app/List/') ||
		window.location.pathname.includes('/app/Form/') ||
		window.location.pathname.includes('/desk')) {
		return;
	}
	
	// Check if patient exists and intake form status
	frappe.call({
		method: 'koraflow_core.api.patient_signup.get_intake_form_status',
		callback: function(r) {
			if (r && r.message) {
				var status = r.message.status;
				var patient_exists = r.message.patient_exists;
				
				// If patient doesn't exist or intake not completed, redirect to intake form
				if (!patient_exists || status === 'not_started' || status === 'draft') {
					// Only redirect if not already on a form page
					if (!window.location.pathname.includes('form') && 
						!window.location.pathname.includes('signup') &&
						!window.location.pathname.includes('login') &&
						!window.location.pathname.includes('/app/')) {
						window.location.href = '/glp1-intake';
					}
				}
			}
		},
		error: function(r) {
			// Silently fail - don't interrupt user experience
			console.log('Intake form status check failed:', r);
		}
	});
}

// Handle intake form submission
function submit_intake_form(form_data) {
	frappe.call({
		method: 'koraflow_core.api.patient_signup.create_patient_from_intake',
		args: {
			intake_data: form_data
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert({
					message: __('Intake form submitted successfully. Creating your patient profile...'),
					indicator: 'green'
				});
				
				// Redirect to patient dashboard
				setTimeout(function() {
					window.location.href = '/app/patient';
				}, 1500);
			} else {
				frappe.show_alert({
					message: __('Error submitting intake form. Please try again.'),
					indicator: 'red'
				});
			}
		},
		error: function(r) {
			frappe.show_alert({
				message: __('Error submitting intake form. Please try again.'),
				indicator: 'red'
			});
		}
	});
}

