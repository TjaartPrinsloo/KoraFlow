// Handle redirect after signup for Patient users
console.log('[SignupRedirect] Script loading...');

// Wait for both frappe and login to be available
(function() {
	function setupRedirect() {
		console.log('[SignupRedirect] Setting up redirect handler...');
		
		// Check if login object exists
		if (typeof login === 'undefined' || !login.login_handlers) {
			console.log('[SignupRedirect] Login object not ready, retrying...');
			setTimeout(setupRedirect, 200);
			return;
		}
		
		console.log('[SignupRedirect] Login object found!');
		
		// Intercept login.call which is what the signup form actually uses
		// This must happen AFTER login object is ready
		function interceptLoginCall() {
			// #region agent log
			var logData = {location:'signup_redirect.js:interceptLoginCall',message:'interceptLoginCall called',data:{loginExists:typeof login !== 'undefined',loginCallExists:typeof login !== 'undefined' && typeof login.call === 'function',alreadyIntercepted:typeof login !== 'undefined' && login.call && login.call._signupRedirectIntercepted},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
			console.log('[DEBUG]', JSON.stringify(logData));
			try {
				var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
				logs.push(logData);
				localStorage.setItem('debug_logs', JSON.stringify(logs));
			} catch(e) {}
			// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
			// #endregion
			if (typeof login !== 'undefined' && login.call && typeof login.call === 'function') {
				// Check if already intercepted
				if (login.call._signupRedirectIntercepted) {
					// #region agent log
					// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:interceptLoginCall',message:'Already intercepted, skipping',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
					// #endregion
					return;
				}
				
				var originalLoginCall = login.call;
				login.call = function(args, callback, url) {
					// #region agent log
					var logData = {location:'signup_redirect.js:login.call',message:'login.call invoked',data:{cmd:args && args.cmd,isSignup:args && args.cmd && (args.cmd.includes('sign_up') || args.cmd === 'frappe.core.doctype.user.user.sign_up')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
					console.log('[DEBUG]', JSON.stringify(logData));
					try {
						var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
						logs.push(logData);
						localStorage.setItem('debug_logs', JSON.stringify(logs));
					} catch(e) {}
					// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
					// #endregion
					// Check if this is a signup call
					if (args && args.cmd && (args.cmd.includes('sign_up') || args.cmd === 'frappe.core.doctype.user.user.sign_up')) {
						console.log('[SignupRedirect] ========== SIGNUP CALL DETECTED (via login.call) ==========');
						console.log('[SignupRedirect] Original cmd:', args.cmd);
						
						// Redirect to custom passwordless signup
						args.cmd = "koraflow_core.api.patient_signup.patient_sign_up";
						if (!args.redirect_to) {
							args.redirect_to = "/glp1-intake/new";
						}
						console.log('[SignupRedirect] Changed cmd to:', args.cmd);
						console.log('[SignupRedirect] Redirect to:', args.redirect_to);
						
						// Passwordless signup - don't add password field
						// addPasswordField(); // DISABLED for passwordless signup
						// Try multiple times to get password
						var password = null;
						for (var i = 0; i < 3; i++) {
							if ($('#signup_password').length) {
								password = $('#signup_password').val();
								if (password) break;
							}
							addPasswordField();
							// Small delay for DOM update
							if (i < 2) {
								var start = Date.now();
								while (Date.now() - start < 50) {} // Small delay
							}
						}
						
						if (password) {
							args.password = password;
							console.log('[SignupRedirect] ✓ Password added to signup args (' + password.length + ' chars)');
						} else {
							console.log('[SignupRedirect] ⚠ No password found in form - API will generate one');
							// Don't add password - API will generate one
						}
						
						console.log('[SignupRedirect] Signup args:', JSON.stringify(args));
						console.log('[SignupRedirect] Callback type:', typeof callback);
						console.log('[SignupRedirect] URL:', url);
						// #region agent log
						// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:login.call',message:'Signup call detected',data:{args:args},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
						// #endregion
						
						// Wrap the callback to intercept the response
						var originalCallback = callback;
						callback = function(r) {
							console.log('[SignupRedirect] ========== SIGNUP RESPONSE (via login.call callback) ==========');
							console.log('[SignupRedirect] Full response:', r);
							console.log('[SignupRedirect] Response message:', r.message);
							console.log('[SignupRedirect] Response message type:', typeof r.message);
							console.log('[SignupRedirect] Response message is array:', Array.isArray(r.message));
							console.log('[SignupRedirect] Response exc:', r.exc);
							console.log('[SignupRedirect] Response status:', r.status);
							// #region agent log
							// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:login.call callback',message:'Signup response received',data:{hasMessage:!!r.message,messageType:typeof r.message,isArray:Array.isArray(r.message),messageValue:r.message,status:r.status,exc:r.exc},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
							// #endregion
						
						// Handle redirect here if needed - check for status 1, 2, or 3
						if (r && r.message && Array.isArray(r.message)) {
							var status = parseInt(r.message[0]);
							if (status === 3 || status === 1 || status === 2) {
								var redirect_url = r.message.length >= 3 ? r.message[2] : '/glp1-intake/new';
								var login_token = r.message.length >= 4 ? r.message[3] : null;
								console.log('[SignupRedirect] ✓ Status', status, 'in login.call callback - Token:', login_token ? 'Present' : 'Missing');
							
							// Auto-login first if token is present
							// Use redirect-based login to ensure cookies are set properly
							if (login_token) {
								console.log('[SignupRedirect] Auto-logging in via redirect (ensures cookies are set)...');
								// Redirect to auto-login endpoint which will perform login and redirect to intake form
								var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
								console.log('[SignupRedirect] →→→ REDIRECTING to auto-login:', auto_login_url);
								// #region agent log
								var logData = {location:'signup_redirect.js:login.call callback',message:'Redirecting to auto-login endpoint',data:{auto_login_url:auto_login_url,redirect_url:redirect_url,has_token:!!login_token},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'};
								console.log('[DEBUG]', JSON.stringify(logData));
								try {
									var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
									logs.push(logData);
									localStorage.setItem('debug_logs', JSON.stringify(logs));
								} catch(e) {}
								// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
								// #endregion
								setTimeout(function() {
									window.location.href = auto_login_url;
								}, 300);
							} else {
								console.log('[SignupRedirect] No token, redirecting directly to:', redirect_url);
								setTimeout(function() {
									window.location.href = redirect_url;
								}, 1000);
							}
							
							// Don't call original callback - we've handled the redirect
							return;
						}
					}
					
					// Call original callback if provided (for non-signup or non-success responses)
					if (originalCallback) {
						originalCallback(r);
					}
				};
			}
			
			// Call original login.call
			return originalLoginCall.call(this, args, callback, url);
		};
		
		// Mark as intercepted
		login.call._signupRedirectIntercepted = true;
		console.log('[SignupRedirect] ✓ login.call intercepted');
		// #region agent log
		// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:interceptLoginCall',message:'login.call interception successful',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
		// #endregion
	} else {
		// Retry if login object not ready
		console.log('[SignupRedirect] login.call not ready, retrying...');
		// #region agent log
		// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:interceptLoginCall',message:'login.call not ready',data:{loginExists:typeof login !== 'undefined',loginCallExists:typeof login !== 'undefined' && typeof login.call === 'function'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
		// #endregion
		setTimeout(interceptLoginCall, 100);
	}
}
		
		// Try to intercept immediately
		interceptLoginCall();
		
		// Also try after a delay to ensure login object is ready
		setTimeout(interceptLoginCall, 500);
		setTimeout(interceptLoginCall, 1000);
		setTimeout(interceptLoginCall, 2000);
		
		// CRITICAL INTERCEPTION: Intercept frappe.call - THIS IS WHERE THE RESPONSE FLOWS
		// login.call() calls frappe.call() with statusCode: login.login_handlers
		// So we need to intercept frappe.call() and wrap the statusCode[200] handler
		if (typeof frappe !== 'undefined' && frappe.call) {
			var originalFrappeCall = frappe.call;
			frappe.call = function(options) {
				// Check if this is a signup call
				var isSignupCall = options.args && options.args.cmd && (options.args.cmd.includes('sign_up') || options.args.cmd === 'frappe.core.doctype.user.user.sign_up');
				if (isSignupCall) {
					console.log('[SignupRedirect] ========== SIGNUP CALL DETECTED (via frappe.call) ==========');
					console.log('[SignupRedirect] Original cmd:', options.args.cmd);
					// Redirect to custom passwordless signup
					options.args.cmd = "koraflow_core.api.patient_signup.patient_sign_up";
					if (!options.args.redirect_to) {
						options.args.redirect_to = "/glp1-intake/new";
					}
					console.log('[SignupRedirect] Changed cmd to:', options.args.cmd);
					console.log('[SignupRedirect] Redirect to:', options.args.redirect_to);
					console.log('[SignupRedirect] Signup args:', JSON.stringify(options.args));
					console.log('[SignupRedirect] Has statusCode:', !!options.statusCode);
					console.log('[SignupRedirect] Has statusCode[200]:', !!(options.statusCode && options.statusCode[200]));
					// #region agent log
					var logData = {location:'signup_redirect.js:frappe.call',message:'Signup call detected',data:{args:options.args,hasStatusCode:!!options.statusCode,statusCode200:!!(options.statusCode && options.statusCode[200])},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
					console.log('[DEBUG]', JSON.stringify(logData));
					try {
						var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
						logs.push(logData);
						localStorage.setItem('debug_logs', JSON.stringify(logs));
					} catch(e) {}
					// #endregion
				}
				
				// Wrap the callback to see the response
				var originalCallback = options.callback;
				// Store whether this was a signup call (check BEFORE we change the cmd)
				var wasSignupCall = isSignupCall;
				options.callback = function(r) {
					// Check if this is a signup response (use stored flag OR check for our custom API)
					if (wasSignupCall || (options.args && options.args.cmd && (options.args.cmd.includes('sign_up') || options.args.cmd.includes('patient_signup')))) {
						console.log('[SignupRedirect] ========== SIGNUP RESPONSE (via callback) ==========');
						console.log('[SignupRedirect] Full response:', r);
						console.log('[SignupRedirect] Response message:', r.message);
						console.log('[SignupRedirect] Response message type:', typeof r.message);
						console.log('[SignupRedirect] Response message is array:', Array.isArray(r.message));
						console.log('[SignupRedirect] Response status:', r.status);
						console.log('[SignupRedirect] Response exc:', r.exc);
						
						// Handle redirect here if needed
						if (r && r.message && Array.isArray(r.message) && r.message[0] == 3) {
							var redirect_url = r.message[2] || '/glp1-intake/new';
							var login_token = r.message.length >= 4 ? r.message[3] : null;
							console.log('[SignupRedirect] ✓ Status 3 in callback - Token:', login_token ? 'Present' : 'Missing');
							
							// Auto-login first if token is present
							// Use redirect-based login to ensure cookies are set properly
							if (login_token) {
								console.log('[SignupRedirect] Auto-logging in via redirect (ensures cookies are set)...');
								// Redirect to auto-login endpoint which will perform login and redirect to intake form
								var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
								console.log('[SignupRedirect] →→→ REDIRECTING to auto-login:', auto_login_url);
								setTimeout(function() {
									window.location.href = auto_login_url;
								}, 300);
							} else {
								console.log('[SignupRedirect] No token, redirecting directly');
							setTimeout(function() {
								window.location.href = redirect_url;
							}, 1000);
							}
						}
					}
					if (originalCallback) {
						originalCallback(r);
					}
				};
				
				// CRITICAL: Wrap statusCode handlers - this is where the response actually goes
				// login.call() passes statusCode: login.login_handlers, so we need to intercept here
				// Ensure statusCode object exists
				if (!options.statusCode) {
					options.statusCode = {};
				}
				
				// Always wrap statusCode[200] if it exists, or create it if this is a signup call
				var isSignupCall = options.args && options.args.cmd && (options.args.cmd.includes('sign_up') || options.args.cmd === 'frappe.core.doctype.user.user.sign_up');
				
				if (options.statusCode[200] || isSignupCall) {
					var original200Handler = options.statusCode[200] || function() {};
					
					if (isSignupCall) {
						console.log('[SignupRedirect] ⚠⚠⚠ WRAPPING statusCode[200] handler for signup call!');
						// #region agent log
						var logData = {location:'signup_redirect.js:frappe.call statusCode',message:'Wrapping statusCode[200] for signup',data:{hasOriginalHandler:!!original200Handler},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
						console.log('[DEBUG]', JSON.stringify(logData));
						try {
							var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
							logs.push(logData);
							localStorage.setItem('debug_logs', JSON.stringify(logs));
						} catch(e) {}
						// #endregion
					}
					
					options.statusCode[200] = function(data, xhr) {
						// Use stored flag OR check for our custom API
						var isSignupResponse = isSignupCall || (options.args && options.args.cmd && (options.args.cmd.includes('sign_up') || options.args.cmd.includes('patient_signup')));
						
						if (isSignupResponse) {
							console.log('[SignupRedirect] ========== STATUS 200 HANDLER (via statusCode) ==========');
							console.log('[SignupRedirect] Data:', data);
							console.log('[SignupRedirect] Data.message:', data.message);
							console.log('[SignupRedirect] Data.message type:', typeof data.message);
							console.log('[SignupRedirect] Data.message is array:', Array.isArray(data.message));
							// #region agent log
							var logData = {location:'signup_redirect.js:statusCode[200]',message:'statusCode[200] handler called for signup',data:{hasMessage:!!data.message,messageType:typeof data.message,isArray:Array.isArray(data.message),messageValue:data.message},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
							console.log('[DEBUG]', JSON.stringify(logData));
							try {
								var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
								logs.push(logData);
								localStorage.setItem('debug_logs', JSON.stringify(logs));
							} catch(e) {}
							// #endregion
							
							// Handle redirect here - check for status 1, 2, or 3
							if (data && data.message && Array.isArray(data.message) && data.message.length >= 2) {
								var statusCode = parseInt(data.message[0]);
								var isOnSignupPage = window.location.hash === '#signup' || window.location.pathname.includes('signup');
								
								// Status 1 = Default Frappe success (but user was created with Patient role) - REDIRECT TO INTAKE
								// Status 2 = Account created, email failed - REDIRECT TO INTAKE
								// Status 3 = Success with redirect
								if ((statusCode === 1 && isOnSignupPage) || statusCode === 2 || statusCode === 3) {
									if (statusCode === 1) {
										console.log('[SignupRedirect] Status 1 detected on signup page - redirecting to intake form');
									}
									// Get redirect URL from response or use default
									var redirect_url = data.message.length >= 3 ? data.message[2] : '/glp1-intake/new';
									var login_token = data.message.length >= 4 ? data.message[3] : null;
									
									console.log('[SignupRedirect] ✓✓✓ Status', statusCode, 'in statusCode handler - Token:', login_token ? 'Present' : 'Missing');
									console.log('[SignupRedirect] Redirect URL:', redirect_url);
									console.log('[SignupRedirect] Message:', data.message[1]);
									
									// Auto-login first if token is present
									// Use redirect-based login to ensure cookies are set properly
									if (login_token) {
										console.log('[SignupRedirect] Auto-logging in via redirect (ensures cookies are set)...');
										// Redirect to auto-login endpoint which will perform login and redirect to intake form
										// This ensures session cookies are properly set
										var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
										console.log('[SignupRedirect] →→→ REDIRECTING to auto-login:', auto_login_url);
										setTimeout(function() {
											window.location.href = auto_login_url;
										}, 300);
										// DON'T call original handler - we've handled it
										return;
									} else {
										console.log('[SignupRedirect] No token, redirecting directly to:', redirect_url);
										setTimeout(function() {
											console.log('[SignupRedirect] Executing redirect NOW to:', redirect_url);
											window.location.href = redirect_url;
										}, 500);
										// DON'T call original handler - we've handled it
										return;
									}
								}
							}
						}
						
						// Call original handler for non-signup or non-status-3 responses
						if (original200Handler) {
							original200Handler(data, xhr);
						}
					};
				}
				
				return originalFrappeCall.call(this, options);
			};
			console.log('[SignupRedirect] ✓ frappe.call intercepted');
		}
		
		// Add password field to signup form - DISABLED for passwordless signup
		function addPasswordField() {
			// DISABLED: Passwordless signup doesn't need password field
			return false;
			if (typeof $ === 'undefined') {
				console.log('[SignupRedirect] jQuery not available for addPasswordField');
				return false;
			}
			
			var signupForm = $('.form-signup');
			if (signupForm.length === 0) {
				console.log('[SignupRedirect] Signup form not found');
				return false;
			}
			
			// Check if password field already exists
			if ($('#signup_password').length > 0) {
				console.log('[SignupRedirect] Password field already exists');
				return true; // Already added
			}
			
			// Try multiple selectors to find the email field
			var emailField = $('#signup_email').closest('.form-group');
			if (emailField.length === 0) {
				// Try alternative selector
				emailField = $('#signup_email').parent();
			}
			if (emailField.length === 0) {
				// Try finding by input type
				emailField = $('.form-signup input[type="email"]').closest('.form-group');
			}
			
			if (emailField.length > 0) {
				var passwordHtml = '<div class="form-group">' +
					'<label class="form-label sr-only" for="signup_password">Password</label>' +
					'<input type="password" id="signup_password" class="form-control" ' +
					'placeholder="Password" required autocomplete="new-password" minlength="6">' +
					'</div>';
				emailField.after(passwordHtml);
				console.log('[SignupRedirect] ✓ Password field added to signup form');
				return true;
			} else {
				console.log('[SignupRedirect] Email field not found. Form structure:', signupForm.html().substring(0, 200));
				return false;
			}
		}
		
		// Also intercept the signup form directly - use multiple methods
		function attachFormListener() {
			if (typeof $ !== 'undefined') {
				// Add password field first - try multiple times
				console.log('[SignupRedirect] attachFormListener called, attempting to add password field...');
				for (var i = 0; i < 3; i++) {
					if (addPasswordField()) break;
					var start = Date.now();
					while (Date.now() - start < 100) {} // Small delay
				}
				
				// Remove any existing listeners to avoid duplicates
				$('.form-signup').off('submit.signupRedirect');
				
				// Attach listener
				$('.form-signup').on('submit.signupRedirect', function(e) {
					console.log('[SignupRedirect] ========== SIGNUP FORM SUBMITTED ==========');
					// Ensure password field exists before submission - try multiple times
					var passwordAdded = false;
					for (var i = 0; i < 5; i++) {
						if (addPasswordField()) {
							passwordAdded = true;
							break;
						}
						// Small delay for DOM update
						var start = Date.now();
						while (Date.now() - start < 50) {}
					}
					if (!passwordAdded) {
						console.log('[SignupRedirect] ⚠ Failed to add password field after 5 attempts');
					}
					var email = $('#signup_email').val();
					var name = $('#signup_fullname').val();
					var password = $('#signup_password').val();
					console.log('[SignupRedirect] Email:', email);
					console.log('[SignupRedirect] Name:', name);
					console.log('[SignupRedirect] Password:', password ? 'Yes (' + password.length + ' chars)' : 'No');
					
					// Also check if login.call exists and log it
					if (typeof login !== 'undefined' && login.call) {
						console.log('[SignupRedirect] login.call is available:', typeof login.call);
					} else {
						console.log('[SignupRedirect] ⚠ login.call NOT available!');
					}
				});
				
				// Also listen for click on signup button
				$('.btn-signup').off('click.signupRedirect');
				$('.btn-signup').on('click.signupRedirect', function(e) {
					console.log('[SignupRedirect] ========== SIGNUP BUTTON CLICKED ==========');
					// Ensure password field is added before allowing submission - try multiple times
					for (var i = 0; i < 3; i++) {
						addPasswordField();
						if ($('#signup_password').length > 0) break;
						// Small delay to ensure DOM is updated
						var start = Date.now();
						while (Date.now() - start < 100) {}
					}
				});
				
				console.log('[SignupRedirect] ✓ Form listeners attached');
			} else {
				// jQuery not ready, try again
				setTimeout(attachFormListener, 100);
			}
		}
		
		// Try to attach immediately
		attachFormListener();
		
		// Also try when DOM is ready
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', attachFormListener);
		}
		
		// Also try with jQuery ready
		if (typeof $ !== 'undefined' && $.ready) {
			$(document).ready(attachFormListener);
		}
		
		// Watch for hash changes to add password field when signup section is shown
		if (typeof $ !== 'undefined') {
			$(window).on('hashchange', function() {
				if (window.location.hash === '#signup') {
					setTimeout(function() {
						console.log('[SignupRedirect] Hash changed to #signup, adding password field...');
						addPasswordField();
					}, 100);
					setTimeout(addPasswordField, 500);
					setTimeout(addPasswordField, 1000);
				}
			});
			
			// Try to add password field periodically when on signup page
			setInterval(function() {
				if (window.location.hash === '#signup' && $('.form-signup').is(':visible')) {
					addPasswordField();
				}
			}, 1000);
			
			// Also try when page loads if already on signup
			if (window.location.hash === '#signup') {
				setTimeout(function() {
					console.log('[SignupRedirect] Already on #signup, adding password field...');
					addPasswordField();
				}, 100);
				setTimeout(addPasswordField, 500);
				setTimeout(addPasswordField, 1000);
				setTimeout(addPasswordField, 2000);
			}
			
			// Also try when DOM is ready
			$(document).ready(function() {
				if (window.location.hash === '#signup') {
					setTimeout(addPasswordField, 200);
					setTimeout(addPasswordField, 1000);
				}
			});
		}
		
		// Store original handler
		var originalHandler = login.login_handlers[200];
		
		console.log('[SignupRedirect] Original 200 handler:', typeof originalHandler);
		console.log('[SignupRedirect] Setting up 200 handler override...');
		console.log('[SignupRedirect] login.login_handlers[200] before override:', typeof login.login_handlers[200]);
		// #region agent log
		// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'signup_redirect.js:setupRedirect',message:'Setting up 200 handler override',data:{originalHandlerType:typeof originalHandler,currentHandlerType:typeof login.login_handlers[200]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
		// #endregion
		
		// Create our handler function (store it so we can detect if it gets overwritten)
		window.our200Handler = function(data, xhr) {
			console.log('[SignupRedirect] ============================================');
			console.log('[SignupRedirect] === 200 Handler CALLED ===');
			console.log('[SignupRedirect] Current hash:', window.location.hash);
			console.log('[SignupRedirect] Current URL:', window.location.href);
			console.log('[SignupRedirect] Full response data:', JSON.stringify(data, null, 2));
			console.log('[SignupRedirect] Data.message:', data.message);
			console.log('[SignupRedirect] Data.message type:', typeof data.message);
			console.log('[SignupRedirect] Data.message is array:', Array.isArray(data.message));
			console.log('[SignupRedirect] Data keys:', Object.keys(data || {}));
			
			// CRITICAL: Check for status 1, 2, or 3 response FIRST, before any other logic
			// Status 1 = Default Frappe success (but user was created with Patient role) - REDIRECT TO INTAKE
			// Status 2 = Account created, email failed - REDIRECT TO INTAKE
			// Status 3 = Success with redirect (our custom signup success)
			if (data && data.message && Array.isArray(data.message) && data.message.length >= 2) {
				var status = parseInt(data.message[0]);
				// If we're on signup page and got status 1, redirect to intake form
				var isOnSignupPage = window.location.hash === '#signup' || window.location.pathname.includes('signup') || window.location.pathname.includes('login');
				console.log('[SignupRedirect] Checking status 1 redirect - status:', status, 'isOnSignupPage:', isOnSignupPage, 'hash:', window.location.hash);
				if (status === 1 && isOnSignupPage) {
					// Default Frappe signup succeeded - redirect to intake form
					console.log('[SignupRedirect] ✓✓✓ Status 1 detected on signup page - redirecting to intake form');
					var redirect_url = '/glp1-intake/new';
					// Show success message briefly
					if (login && login.set_status) {
						login.set_status('Account created! Redirecting...', 'green');
					}
					// For status 1, there's no token, so redirect directly
					console.log('[SignupRedirect] No token for status 1, redirecting directly to:', redirect_url);
					setTimeout(function() {
						console.log('[SignupRedirect] →→→ REDIRECTING to intake form:', redirect_url);
						window.location.href = redirect_url;
					}, 800);
					// Don't call original handler - we've handled it
					return;
				}
				if (status === 2 || status === 3) {
					console.log('[SignupRedirect] ✓✓✓ STATUS', status, 'DETECTED IN 200 HANDLER!');
					var message = data.message[1] || 'Account created successfully';
					// For status 2, redirect URL might not be in response, use default
									var redirect_url = data.message.length >= 3 ? data.message[2] : '/glp1-intake/new';
					var login_token = data.message.length >= 4 ? data.message[3] : null;
					
					console.log('[SignupRedirect] Message:', message);
					console.log('[SignupRedirect] Redirect URL:', redirect_url);
					console.log('[SignupRedirect] Login Token:', login_token ? 'Present' : 'Missing');
					
					// Set status
					if (login && login.set_status) {
						login.set_status('Success', 'green');
					}
					
					// Show message briefly
					if (typeof frappe !== 'undefined' && frappe.show_alert) {
						frappe.show_alert({
							message: message,
							indicator: 'green'
						}, 2);
					}
					
					// If we have a login token, auto-login the user first
					// Use redirect-based login to ensure cookies are set properly
					if (login_token) {
						console.log('[SignupRedirect] Auto-logging in via redirect (ensures cookies are set)...');
						// Redirect to auto-login endpoint which will perform login and redirect to intake form
						var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
						console.log('[SignupRedirect] →→→ REDIRECTING to auto-login:', auto_login_url);
						setTimeout(function() {
							window.location.href = auto_login_url;
						}, 300);
						// DON'T call original handler - we've handled it
						return;
					} else {
						// No token, redirect directly to intake wizard
						console.log('[SignupRedirect] No login token, redirecting directly to:', redirect_url);
						setTimeout(function() {
							console.log('[SignupRedirect] Executing redirect NOW to:', redirect_url);
							window.location.href = redirect_url;
						}, 500);
						// DON'T call original handler - we've handled it
						return;
					}
				}
			}
			// #region agent log
			var logData = {location:'signup_redirect.js:200 handler',message:'200 handler called',data:{hash:window.location.hash,url:window.location.href,hasMessage:!!data.message,messageType:typeof data.message,isArray:Array.isArray(data.message),messageValue:data.message,dataKeys:Object.keys(data || {})},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
			console.log('[DEBUG]', JSON.stringify(logData));
			try {
				var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
				logs.push(logData);
				localStorage.setItem('debug_logs', JSON.stringify(logs));
			} catch(e) {}
			// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
			// #endregion
			
			// Check if this is a signup response
			// ALWAYS check if data.message is an array with status 3 (our custom signup success)
			// This is the most reliable way to detect our custom signup response
			var isSignupResponse = false;
			var isOurCustomSignup = false;
			
			if (data.message && Array.isArray(data.message) && data.message.length >= 2) {
				var status = parseInt(data.message[0]);
				// Status 2 = Account created, email failed - REDIRECT TO INTAKE
				// Status 3 = Success with redirect (our custom signup success)
				if (status === 2 || status === 3) {
					isOurCustomSignup = true;
					isSignupResponse = true;
				} else if (window.location.hash === '#signup' || window.location.pathname.includes('signup') || window.location.pathname.includes('login')) {
					// Also handle standard signup responses when on signup page
					isSignupResponse = true;
					console.log('[SignupRedirect] Marked as signup response based on page location');
				}
			} else if (window.location.hash === '#signup' || window.location.pathname.includes('signup') || window.location.pathname.includes('login')) {
				// Fallback: if we're on signup page, treat as signup response
				isSignupResponse = true;
				console.log('[SignupRedirect] Marked as signup response (fallback) based on page location');
			}
			
			console.log('[SignupRedirect] Is signup response?', isSignupResponse, 'Is our custom signup?', isOurCustomSignup);
			// #region agent log
			var logData = {location:'signup_redirect.js:200 handler',message:'Checking if signup response',data:{hash:window.location.hash,hashMatch:window.location.hash === '#signup',hasMessage:!!data.message,messageIsArray:Array.isArray(data.message),messageValue:data.message,messageLength:data.message && data.message.length,status:data.message && Array.isArray(data.message) ? parseInt(data.message[0]) : null,isSignupResponse:isSignupResponse,isOurCustomSignup:isOurCustomSignup},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
			console.log('[DEBUG]', JSON.stringify(logData));
			try {
				var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
				logs.push(logData);
				localStorage.setItem('debug_logs', JSON.stringify(logs));
			} catch(e) {}
			// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
			// #endregion
			
			// PRIORITY: Handle our custom signup response (status 2 or 3) FIRST
			if (isOurCustomSignup) {
				var status = parseInt(data.message[0]);
				console.log('[SignupRedirect] ✓✓✓ OUR CUSTOM SIGNUP RESPONSE DETECTED (Status', status, ')!');
				var message = data.message[1] || 'Account created successfully';
				// For status 2, redirect URL might not be in response, use default
									var redirect_url = data.message.length >= 3 ? data.message[2] : '/glp1-intake/new';
				var login_token = data.message.length >= 4 ? data.message[3] : null;
				
				console.log('[SignupRedirect] Message:', message);
				console.log('[SignupRedirect] Redirect URL:', redirect_url);
				console.log('[SignupRedirect] Login Token:', login_token ? 'Present' : 'Missing');
				
				// Set status
				if (login && login.set_status) {
					login.set_status('Success', 'green');
				}
				
				// Show message briefly
				if (typeof frappe !== 'undefined' && frappe.show_alert) {
					frappe.show_alert({
						message: message,
						indicator: 'green'
					}, 2);
				}
				
				// If we have a login token, auto-login the user first
				if (login_token && typeof frappe !== 'undefined' && frappe.call) {
					console.log('[SignupRedirect] Auto-logging in user with token...');
					frappe.call({
						method: 'koraflow_core.api.auto_login.auto_login_with_token',
						type: 'POST',
						args: {
							token: login_token
						},
						callback: function(r) {
							if (r.message && r.message.success) {
								console.log('[SignupRedirect] ✓ Auto-login successful!');
								console.log('[SignupRedirect] →→→ REDIRECTING to:', redirect_url);
								// Redirect after successful login
								setTimeout(function() {
									window.location.href = redirect_url;
								}, 300);
							} else {
								console.log('[SignupRedirect] ⚠ Auto-login failed, redirecting with token in URL');
								// Fallback: redirect with token in URL
								setTimeout(function() {
									window.location.href = redirect_url + '?signup_token=' + encodeURIComponent(login_token);
								}, 500);
							}
						},
						error: function(r) {
							console.log('[SignupRedirect] ⚠ Auto-login error, redirecting with token in URL');
							// Fallback: redirect with token in URL
							setTimeout(function() {
								window.location.href = redirect_url + '?signup_token=' + encodeURIComponent(login_token);
							}, 500);
						}
					});
				} else {
					// No token, redirect directly
					console.log('[SignupRedirect] No login token, redirecting directly');
					setTimeout(function() {
						window.location.href = redirect_url;
					}, 500);
				}
				
				// Don't call original handler - we've handled it
				return;
			}
			
			if (isSignupResponse) {
				console.log('[SignupRedirect] ✓ Signup response detected!');
				console.log('[SignupRedirect] Data.message:', data.message);
				console.log('[SignupRedirect] Data.message type:', typeof data.message);
				console.log('[SignupRedirect] Is array:', Array.isArray(data.message));
				
				// PREVENT default handler from running for signup responses
				// We'll handle it ourselves
				
				// Handle array response [status, message, redirect_url]
				// Frappe's login.js expects data.message to be an array for signup
				if (Array.isArray(data.message) && data.message.length >= 2) {
					var status = parseInt(data.message[0]);
					console.log('[SignupRedirect] Status code:', status);
					
					// Handle ALL status codes for signup (0, 1, 2, 3)
					if (status === 0) {
						// Error case - let default handler show error
						console.log('[SignupRedirect] Status 0 (error), letting default handler show error');
						if (originalHandler) {
							originalHandler.call(this, data);
						}
						return;
					}
					
					// Status 2 = Account created, email failed - REDIRECT TO INTAKE
					// Status 3 = Success with redirect (our custom status)
					if (status === 2 || status === 3) {
						var message = data.message[1] || 'Account created successfully';
						// For status 2, redirect URL might not be in response, use default
						var redirect_url = data.message.length >= 3 ? data.message[2] : '/glp1-intake/new';
						var login_token = data.message.length >= 4 ? data.message[3] : null;
						
						console.log('[SignupRedirect] ✓✓✓ Status', status, 'detected!');
						console.log('[SignupRedirect] Message:', message);
						console.log('[SignupRedirect] Redirect URL:', redirect_url);
						console.log('[SignupRedirect] Login Token:', login_token ? 'Present' : 'Missing');
						
						// Set status
						if (login && login.set_status) {
							login.set_status('Success', 'green');
						}
						
						// Show message briefly
						if (typeof frappe !== 'undefined' && frappe.show_alert) {
							frappe.show_alert({
								message: message,
								indicator: 'green'
							}, 2);
						}
						
						// If we have a login token, auto-login the user first
						// Use redirect-based login to ensure cookies are set properly
						if (login_token) {
							console.log('[SignupRedirect] Auto-logging in via redirect (ensures cookies are set)...');
							// Redirect to auto-login endpoint which will perform login and redirect to intake form
							var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
							console.log('[SignupRedirect] →→→ REDIRECTING to auto-login:', auto_login_url);
							setTimeout(function() {
								window.location.href = auto_login_url;
							}, 300);
						} else {
							// No token, redirect directly
							console.log('[SignupRedirect] No login token, redirecting directly');
							setTimeout(function() {
						window.location.href = redirect_url;
							}, 500);
						}
						
						// Don't call original handler - we've handled it
						return;
					}
					// Status 1 = Standard success (but we still want to redirect)
					else if (status === 1) {
						console.log('[SignupRedirect] ✓✓✓ Standard success status (1) - redirecting to intake form');
						var message = data.message[1] || 'Account created successfully';
						var redirect_url = data.message.length >= 3 ? data.message[2] : '/glp1-intake/new';
						var login_token = data.message.length >= 4 ? data.message[3] : null;
						
						console.log('[SignupRedirect] Message:', message);
						console.log('[SignupRedirect] Redirect URL:', redirect_url);
						console.log('[SignupRedirect] Login Token:', login_token ? 'Present' : 'Missing');
						
						// Show success message
						if (login && login.set_status) {
							login.set_status('Account created! Redirecting...', 'green');
						}
						
						if (typeof frappe !== 'undefined' && frappe.show_alert) {
							frappe.show_alert({
								message: 'Account created! Redirecting to intake form...',
								indicator: 'green'
							}, 2);
						}
						
						// Try to auto-login if we have a token
						// Use API endpoint instead of page route (page route may not be registered)
						if (login_token) {
							console.log('[SignupRedirect] Auto-logging in via API endpoint (status 1, ensures cookies are set)...');
							// Use API endpoint which handles redirects properly
							var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url || '/glp1-intake/new');
							console.log('[SignupRedirect] →→→ REDIRECTING to auto-login API:', auto_login_url);
							setTimeout(function() {
								window.location.href = auto_login_url;
							}, 300);
							// Don't call original handler - we've handled it
							return;
						} else {
							// No token, but still redirect to intake form
							console.log('[SignupRedirect] No token (status 1), redirecting directly to intake form');
							setTimeout(function() {
								console.log('[SignupRedirect] →→→ REDIRECTING NOW to:', redirect_url || '/glp1-intake/new');
								window.location.href = redirect_url || '/glp1-intake/new';
							}, 800);
							// Don't call original handler - we've handled it
							return;
						}
					}
				}
				// Fallback: if message is a string containing "successfully" or "redirecting"
				else if (data.message && typeof data.message === 'string') {
					if (data.message.toLowerCase().includes('successfully') || 
					    data.message.toLowerCase().includes('redirecting')) {
						console.log('[SignupRedirect] Fallback: String message with success keywords, redirecting');
						setTimeout(function() {
							window.location.href = '/glp1-intake/new';
						}, 500);
						return;
					}
				}
			}
			
			// Call original handler for all other cases
			console.log('[SignupRedirect] Calling original handler for non-signup or unhandled response');
			if (originalHandler) {
				originalHandler.call(this, data);
			}
		};
		
		// Override the 200 handler - MUST run BEFORE Frappe's default handler
		login.login_handlers[200] = window.our200Handler;
		
		// Monitor if handler gets overwritten
		var checkHandler = setInterval(function() {
			if (login.login_handlers[200] !== window.our200Handler) {
				// #region agent log
				var logData = {location:'signup_redirect.js:setupRedirect',message:'200 handler was overwritten!',data:{expectedHandler:typeof window.our200Handler,actualHandler:typeof login.login_handlers[200]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'};
				console.log('[DEBUG]', JSON.stringify(logData));
				try {
					var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
					logs.push(logData);
					localStorage.setItem('debug_logs', JSON.stringify(logs));
				} catch(e) {}
				// #endregion
				console.log('[SignupRedirect] ⚠⚠⚠ 200 handler was overwritten! Restoring...');
				login.login_handlers[200] = window.our200Handler;
			}
		}, 100);
		
		// Store reference for later use
		login.login_handlers._original_200 = originalHandler;
		
		console.log('[SignupRedirect] login.login_handlers[200] after override:', typeof login.login_handlers[200]);
		console.log('[SignupRedirect] ✓ Handler override complete!');
		// #region agent log
		var logData = {location:'signup_redirect.js:setupRedirect',message:'200 handler override complete',data:{handlerType:typeof login.login_handlers[200]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
		console.log('[DEBUG]', JSON.stringify(logData));
		try {
			var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
			logs.push(logData);
			localStorage.setItem('debug_logs', JSON.stringify(logs));
		} catch(e) {}
		// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
		// #endregion
		
		// Monitor for page navigation
		var currentUrl = window.location.href;
		setInterval(function() {
			if (window.location.href !== currentUrl) {
				// #region agent log
				var logData = {location:'signup_redirect.js:setupRedirect',message:'Page navigation detected',data:{from:currentUrl,to:window.location.href},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
				console.log('[DEBUG]', JSON.stringify(logData));
				try {
					var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
					logs.push(logData);
					localStorage.setItem('debug_logs', JSON.stringify(logs));
				} catch(e) {}
				// // fetch('http://127.0.0.1:7244/ingest/6e70ac8b-e9c1-4181-820e-12dae0e65fc1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch((e)=>console.error('[DEBUG] Log fetch failed:',e));
				// #endregion
				currentUrl = window.location.href;
			}
		}, 100);
	}
	
	// Intercept frappe.call IMMEDIATELY when frappe is available (don't wait for login object)
	// This ensures we catch signup responses even if login object isn't ready
	function interceptFrappeCall() {
		if (typeof frappe !== 'undefined' && frappe.call && !frappe.call._signupRedirectIntercepted) {
			var originalFrappeCall = frappe.call;
			frappe.call = function(options) {
				// Check if this is a signup call
				var isSignupCall = options.args && options.args.cmd && (options.args.cmd.includes('sign_up') || options.args.cmd === 'frappe.core.doctype.user.user.sign_up');
				if (isSignupCall) {
					console.log('[SignupRedirect] ========== SIGNUP CALL DETECTED (via frappe.call - early intercept) ==========');
					
					// Wrap the callback to see the response
					var originalCallback = options.callback;
					options.callback = function(r) {
						// Check if this is a signup response with status 3
						if (r && r.message && Array.isArray(r.message) && parseInt(r.message[0]) === 3) {
							var redirect_url = r.message[2] || '/glp1-intake/new';
							var login_token = r.message.length >= 4 ? r.message[3] : null;
							console.log('[SignupRedirect] ✓✓✓ Status 3 detected in early frappe.call intercept - Token:', login_token ? 'Present' : 'Missing');
							
							// Auto-login first if token is present
							if (login_token) {
								console.log('[SignupRedirect] Redirecting to auto-login endpoint...');
								var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
								setTimeout(function() {
									window.location.href = auto_login_url;
								}, 300);
								// Don't call original callback - we've handled it
								return;
							} else {
								console.log('[SignupRedirect] No token, redirecting directly to:', redirect_url);
								setTimeout(function() {
									window.location.href = redirect_url;
								}, 500);
								// Don't call original callback - we've handled it
								return;
							}
						}
						// Call original callback for non-status-3 responses
						if (originalCallback) {
							originalCallback(r);
						}
					};
					
					// Wrap statusCode[200] handler
					if (!options.statusCode) {
						options.statusCode = {};
					}
					var original200Handler = options.statusCode[200] || function() {};
					options.statusCode[200] = function(data, xhr) {
						// Check if this is a signup response with status 3
						if (data && data.message && Array.isArray(data.message) && parseInt(data.message[0]) === 3) {
							var redirect_url = data.message[2] || '/glp1-intake/new';
							var login_token = data.message.length >= 4 ? data.message[3] : null;
							console.log('[SignupRedirect] ✓✓✓ Status 3 detected in statusCode[200] (early intercept) - Token:', login_token ? 'Present' : 'Missing');
							
							// Auto-login first if token is present
							if (login_token) {
								console.log('[SignupRedirect] Redirecting to auto-login endpoint...');
								var auto_login_url = '/api/method/koraflow_core.api.auto_login.auto_login_with_token?token=' + encodeURIComponent(login_token) + '&redirect_to=' + encodeURIComponent(redirect_url);
								setTimeout(function() {
									window.location.href = auto_login_url;
								}, 300);
								// Don't call original handler - we've handled it
								return;
							} else {
								console.log('[SignupRedirect] No token, redirecting directly to:', redirect_url);
								setTimeout(function() {
									window.location.href = redirect_url;
								}, 500);
								// Don't call original handler - we've handled it
								return;
							}
						}
						// Call original handler for non-status-3 responses
						if (original200Handler) {
							original200Handler(data, xhr);
						}
					};
				}
				
				return originalFrappeCall.call(this, options);
			};
			frappe.call._signupRedirectIntercepted = true;
			console.log('[SignupRedirect] ✓ frappe.call intercepted early (before login object ready)');
		}
	}
	
	// Try to intercept frappe.call immediately
	interceptFrappeCall();
	// Also try when frappe becomes available
	if (typeof frappe === 'undefined') {
		var frappeCheckInterval = setInterval(function() {
			if (typeof frappe !== 'undefined') {
				interceptFrappeCall();
				clearInterval(frappeCheckInterval);
			}
		}, 50);
		// Stop checking after 5 seconds
		setTimeout(function() {
			clearInterval(frappeCheckInterval);
		}, 5000);
	}
	
	// Try to setup immediately, but keep retrying to ensure we run AFTER Frappe's login.js
	var setupAttempts = 0;
	var maxAttempts = 30; // Try for 3 seconds (30 * 100ms)
	
	function trySetup() {
		setupAttempts++;
		// #region agent log
		var logData = {location:'signup_redirect.js:trySetup',message:'Attempting setup',data:{attempt:setupAttempts,readyState:document.readyState,hasLogin:typeof login !== 'undefined',hasLoginHandlers:typeof login !== 'undefined' && typeof login.login_handlers !== 'undefined'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
		console.log('[DEBUG]', JSON.stringify(logData));
		try {
			var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
			logs.push(logData);
			localStorage.setItem('debug_logs', JSON.stringify(logs));
		} catch(e) {}
		// #endregion
		
		if (typeof login !== 'undefined' && typeof login.login_handlers !== 'undefined') {
			// Login handlers are ready, set up our override
		setupRedirect();
			// Keep monitoring to ensure our handler stays in place
			var monitorInterval = setInterval(function() {
				if (typeof login !== 'undefined' && login.login_handlers && typeof window.our200Handler !== 'undefined' && login.login_handlers[200] !== window.our200Handler) {
					console.log('[SignupRedirect] ⚠ Handler was overwritten, restoring...');
					login.login_handlers[200] = window.our200Handler;
				}
			}, 200);
			// Stop monitoring after 10 seconds (we should be done by then)
			setTimeout(function() {
				clearInterval(monitorInterval);
			}, 10000);
		} else if (setupAttempts < maxAttempts) {
			// Not ready yet, try again
			setTimeout(trySetup, 100);
	} else {
			// Max attempts reached, try anyway
			console.log('[SignupRedirect] ⚠ Max setup attempts reached, setting up anyway');
			setupRedirect();
	}
	}
	
	// Start trying to setup
	trySetup();
})();

console.log('[SignupRedirect] Script loaded');

