// Pre-populate email field with logged-in user's email for GLP-1 Intake Form
console.log('[GLP1 Intake JS] Script loading...');

(function() {
	function populateEmail() {
		console.log('[GLP1 Intake JS] populateEmail called');
		
		if (frappe.session && frappe.session.user && frappe.session.user !== 'Guest') {
			console.log('[GLP1 Intake JS] User:', frappe.session.user);
			
			// Check if we're on the intake form page
			if (window.location.pathname.indexOf('glp1-intake') === -1) {
				console.log('[GLP1 Intake JS] Not on intake form page');
				return;
			}
			
			// Try multiple selectors to find the email field
			var emailField = $('[data-fieldname="email"] input[type="text"], [data-fieldname="email"] input[type="email"], [data-fieldname="email"] .control-value, .frappe-control[data-fieldname="email"] input, .frappe-control[data-fieldname="email"] .control-value');
			
			console.log('[GLP1 Intake JS] Found email fields:', emailField.length);
			
			if (emailField.length) {
				var currentValue = emailField.val() || emailField.text() || '';
				console.log('[GLP1 Intake JS] Current value:', currentValue);
				
				if (!currentValue || currentValue.trim() === '') {
					// Set the email value
					if (emailField.is('input')) {
						emailField.val(frappe.session.user);
						emailField.trigger('change');
						emailField.trigger('input');
						console.log('[GLP1 Intake] Email field populated with:', frappe.session.user);
					} else {
						// For read-only fields that use .control-value
						emailField.text(frappe.session.user);
						// Also try to find and update the hidden input
						var hiddenInput = emailField.closest('.frappe-control').find('input[type="hidden"]');
						if (hiddenInput.length) {
							hiddenInput.val(frappe.session.user);
						}
						// Try to find the actual input field
						var actualInput = emailField.closest('.frappe-control').find('input[type="text"], input[type="email"]');
						if (actualInput.length) {
							actualInput.val(frappe.session.user);
							actualInput.trigger('change');
							actualInput.trigger('input');
							console.log('[GLP1 Intake] Email field populated with:', frappe.session.user);
						}
					}
				} else {
					console.log('[GLP1 Intake JS] Email field already has value:', currentValue);
				}
			} else {
				console.log('[GLP1 Intake JS] Email field not found, will retry');
				// Retry after a short delay if field not found yet
				setTimeout(populateEmail, 500);
			}
		} else {
			console.log('[GLP1 Intake JS] User not logged in or Guest');
		}
	}
	
	// Override web form success handler to redirect to /me
	if (typeof frappe !== 'undefined' && frappe.web_form) {
		var originalHandleSuccess = frappe.web_form.WebForm.prototype.handle_success;
		frappe.web_form.WebForm.prototype.handle_success = function(data) {
			// Check if this is the intake form
			if (this.name === 'glp1-intake' || this.name === 'glp-1-intake-form' || window.location.pathname.indexOf('glp1-intake') !== -1) {
				console.log('[GLP1 Intake JS] Redirecting to /me after form submission');
				// Redirect to my account page
				setTimeout(function() {
					window.location.href = '/me';
				}, 500);
			} else {
				// Call original handler for other forms
				if (originalHandleSuccess) {
					originalHandleSuccess.call(this, data);
				}
			}
		};
	}
	
	// Wait for frappe to be ready
	if (typeof frappe !== 'undefined' && typeof frappe.ready === 'function') {
		frappe.ready(function() {
			console.log('[GLP1 Intake JS] frappe.ready called');
			setTimeout(populateEmail, 500);
			setTimeout(populateEmail, 1500);
			setTimeout(populateEmail, 3000);
		});
	} else {
		console.log('[GLP1 Intake JS] Using document.ready fallback');
		// Fallback if frappe.ready is not available
		$(document).ready(function() {
			setTimeout(populateEmail, 1000);
			setTimeout(populateEmail, 2500);
			setTimeout(populateEmail, 4000);
		});
	}
})();
