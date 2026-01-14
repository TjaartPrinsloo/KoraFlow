// Patient signup form - NO password collection, email verification required
// Run immediately, don't wait for frappe.ready
(function () {
	console.log('[SignupForm] Script loading...');

	// Remove any password fields that might exist
	function removePasswordField() {
		$('#signup_password').closest('.form-group').remove();
	}

	// Function to setup signup handler
	function setupSignupHandler() {
		console.log('[SignupForm] Setting up signup handler...');

		// CRITICAL: Unbind Frappe's default signup handler first
		// This ensures our handler runs instead of the default one
		$(".form-signup").off("submit");

		// Override the signup form submit handler with higher priority
		// Use direct binding (not document.on) to ensure it runs first
		$(".form-signup").on("submit", function (event) {
			console.log('[SignupForm] ========== FORM SUBMIT INTERCEPTED ==========');
			event.preventDefault();
			event.stopPropagation();
			event.stopImmediatePropagation();

			var args = {};
			// Use custom passwordless patient signup directly
			args.cmd = "koraflow_core.api.patient_signup.patient_sign_up";
			args.email = ($("#signup_email").val() || "").trim();
			args.full_name = frappe.utils.xss_sanitise(($("#signup_fullname").val() || "").trim());
			// Logic to determine redirect URL
			var urlParamRedirect = frappe.utils.get_url_arg("redirect-to");
			var cleanRedirect = frappe.utils.sanitise_redirect(urlParamRedirect);

			// For patients, we NEVER want them to go to /app (Desk)
			// If no redirect provided, OR if it tries to go to /app, force the intake form
			if (!cleanRedirect || cleanRedirect.indexOf("/app") === 0) {
				args.redirect_to = "/glp1-intake/new";
			} else {
				args.redirect_to = cleanRedirect;
			}

			console.log('[SignupForm] Patient signup submitted (no password)', args);

			// Simple email validation regex
			function validateEmail(email) {
				const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
				return re.test(email);
			}

			// Validate inputs
			if (!args.email || !validateEmail(args.email) || !args.full_name) {
				if (typeof login !== 'undefined' && login.set_status) {
					login.set_status("Valid email and name required", 'red');
				} else {
					frappe.msgprint("Valid email and name required");
				}
				return false;
			}

			// Call passwordless patient signup API directly
			frappe.call({
				method: "koraflow_core.api.patient_signup.patient_sign_up",
				args: args,
				callback: function (r) {
					if (r.message) {
						var status = Array.isArray(r.message) ? parseInt(r.message[0]) : 0;
						var message = Array.isArray(r.message) && r.message.length >= 2 ? r.message[1] : "";
						var redirectUrl = Array.isArray(r.message) && r.message.length >= 3 ? r.message[2] : null;
						var loginToken = Array.isArray(r.message) && r.message.length >= 4 ? r.message[3] : null;

						console.log('[SignupForm] Response:', { status: status, message: message, redirectUrl: redirectUrl, hasToken: !!loginToken });

						if (status === 1 || status === 2 || status === 3) {
							// Success - account created
							if (typeof login !== 'undefined' && login.set_status) {
								login.set_status(message || "Account created successfully", 'green');
							} else {
								frappe.msgprint(message || "Account created successfully");
							}

							// If we have a login token, use it for auto-login
							if (loginToken) {
								console.log('[SignupForm] Auto-logging in with token...');
								frappe.call({
									method: 'koraflow_core.api.auto_login.auto_login_with_token',
									args: {
										token: loginToken,
										redirect_to: redirectUrl || "/glp1-intake-wizard"
									},
									callback: function (loginResult) {
										if (loginResult.message && loginResult.message.success) {
											console.log('[SignupForm] Auto-login successful, redirecting...');
											window.location.href = redirectUrl || "/glp1-intake-wizard";
										} else {
											console.log('[SignupForm] Auto-login failed, redirecting with token in URL');
											window.location.href = (redirectUrl || "/glp1-intake-wizard") + "?signup_token=" + encodeURIComponent(loginToken);
										}
									},
									error: function () {
										console.log('[SignupForm] Auto-login error, redirecting with token in URL');
										window.location.href = (redirectUrl || "/glp1-intake-wizard") + "?signup_token=" + encodeURIComponent(loginToken);
									}
								});
							} else {
								// No token, redirect directly
								var finalRedirectUrl = redirectUrl || "/glp1-intake-wizard";
								console.log('[SignupForm] No login token, redirecting directly to:', finalRedirectUrl);
								setTimeout(function () {
									window.location.href = finalRedirectUrl;
								}, 500);
							}
						} else {
							// Error
							var errorMsg = message || "Signup failed";
							if (typeof login !== 'undefined' && login.set_status) {
								login.set_status(errorMsg, 'red');
							} else {
								frappe.msgprint(errorMsg);
							}
						}
					}
				},
				error: function (r) {
					console.error('[SignupForm] Signup error:', r);
					var errorMsg = r.message || r.exc || "Signup failed. Please try again.";
					if (typeof login !== 'undefined' && login.set_status) {
						login.set_status(errorMsg, 'red');
					} else {
						frappe.msgprint(errorMsg);
					}
				}
			});

			return false;
		});
	}

	// Wait for jQuery and Frappe to be ready
	function initWhenReady() {
		if (typeof $ !== 'undefined' && $.fn.on && typeof frappe !== 'undefined') {
			console.log('[SignupForm] jQuery and Frappe ready, setting up handler...');
			setupSignupHandler();
			removePasswordField();
		} else {
			console.log('[SignupForm] Waiting for jQuery/Frappe...', {
				hasJQuery: typeof $ !== 'undefined',
				hasFrappe: typeof frappe !== 'undefined'
			});
			setTimeout(initWhenReady, 100);
		}
	}

	// Try immediately
	initWhenReady();

	// Also try on document ready
	if (typeof $ !== 'undefined') {
		$(document).ready(function () {
			console.log('[SignupForm] Document ready, setting up handler...');
			setupSignupHandler();
			removePasswordField();
		});
	}

	// Also try after frappe.ready
	if (typeof frappe !== 'undefined' && frappe.ready) {
		frappe.ready(function () {
			console.log('[SignupForm] Frappe ready, setting up handler...');
			setupSignupHandler();
			removePasswordField();
			setTimeout(removePasswordField, 500);
			setTimeout(removePasswordField, 1000);
		});
	}

	// Watch for hash changes (only if jQuery is available)
	if (typeof $ !== 'undefined') {
		$(window).on('hashchange', function () {
			if (window.location.hash === '#signup') {
				setTimeout(function () {
					setupSignupHandler();
					removePasswordField();
				}, 100);
			}
		});
	}
})();
