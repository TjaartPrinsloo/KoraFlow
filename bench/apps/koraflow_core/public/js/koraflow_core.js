/**
 * KoraFlow Core JavaScript
 * Frontend branding and module management
 */

// IMMEDIATE redirect check - must run BEFORE Frappe initializes
// This runs as soon as the script loads, before frappe.ready
(function () {
	if (typeof window !== 'undefined' && window.location) {
		const path = window.location.pathname;

		// Check if we're on a route that should redirect
		if (path === "/app/build" || path === "/app/home" || path === "/app/user-profile" || path === "/app/sales-agent-dashboard") {
			// Function to check if user is Sales Agent
			function isSalesAgentUser() {
				// Debug logging
				console.log('[KoraFlow] Checking if user is Sales Agent, path:', path);

				// Try to get user info from localStorage (Frappe stores boot info there)
				try {
					const bootInfo = localStorage.getItem('bootinfo');
					if (bootInfo) {
						const boot = JSON.parse(bootInfo);
						console.log('[KoraFlow] Boot info from localStorage:', boot);
						if (boot && boot.user && boot.user.roles) {
							const roles = boot.user.roles || [];
							console.log('[KoraFlow] User roles from localStorage:', roles);
							const isAgent = roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
							if (isAgent) return true;
						}
					}
				} catch (e) {
					console.log('[KoraFlow] Error reading bootinfo from localStorage:', e);
				}

				// Also check if boot info is in window (sometimes Frappe puts it there)
				if (typeof window !== 'undefined' && window.boot && window.boot.user && window.boot.user.roles) {
					const roles = window.boot.user.roles || [];
					console.log('[KoraFlow] User roles from window.boot:', roles);
					const isAgent = roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
					if (isAgent) return true;
				}

				// Check frappe.boot if available
				if (typeof frappe !== 'undefined' && frappe.boot && frappe.boot.user && frappe.boot.user.roles) {
					const roles = frappe.boot.user.roles || [];
					console.log('[KoraFlow] User roles from frappe.boot:', roles);
					const isAgent = roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
					if (isAgent) return true;
				}

				// Fallback: Check page title (if it contains "Sales Agent")
				if (document.title && document.title.toLowerCase().includes("sales agent")) {
					console.log('[KoraFlow] Detected Sales Agent from page title:', document.title);
					return true;
				}

				console.log('[KoraFlow] User is NOT a Sales Agent');
				return false;
			}

			// Function to redirect if user is Sales Agent
			function checkAndRedirect() {
				if (isSalesAgentUser()) {
					console.log('[KoraFlow] User is Sales Agent, redirecting to /sales_agent_dashboard');
					window.location.replace("/sales_agent_dashboard");
					return true;
				}
				return false;
			}

			// Check immediately
			if (checkAndRedirect()) {
				return;
			}

			// Check multiple times with increasing delays
			var checkDelays = [50, 100, 200, 500, 1000, 1500, 2000];
			checkDelays.forEach(function (delay) {
				setTimeout(function () {
					checkAndRedirect();
				}, delay);
			});

			// Also check when frappe.boot becomes available
			if (typeof frappe !== 'undefined') {
				const checkInterval = setInterval(function () {
					if (checkAndRedirect()) {
						clearInterval(checkInterval);
					}
				}, 100);

				// Stop checking after 5 seconds
				setTimeout(function () {
					clearInterval(checkInterval);
				}, 5000);
			} else {
				// Wait for frappe to load
				var frappeCheckInterval = setInterval(function () {
					if (typeof frappe !== 'undefined') {
						clearInterval(frappeCheckInterval);
						const checkInterval = setInterval(function () {
							if (checkAndRedirect()) {
								clearInterval(checkInterval);
							}
						}, 100);
						setTimeout(function () {
							clearInterval(checkInterval);
						}, 5000);
					}
				}, 50);
				setTimeout(function () {
					clearInterval(frappeCheckInterval);
				}, 5000);
			}
		}
	}
})();

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
koraflow.applyBranding = function (text) {
	if (!text) return text;

	let branded = text;
	for (const [original, branded_name] of Object.entries(koraflow.branding)) {
		branded = branded.replace(new RegExp(original, 'g'), branded_name);
	}
	return branded;
};

// Disable app logo link for Sales Agents (but keep it visible)
// This must run IMMEDIATELY, not in frappe.ready, to catch clicks before Frappe's router
(function () {
	function isSalesAgent() {
		// Check frappe.boot if available
		if (typeof frappe !== 'undefined' && frappe.boot && frappe.boot.user) {
			const roles = frappe.boot.user.roles || [];
			return roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
		}

		// Check localStorage bootinfo
		try {
			const bootInfo = localStorage.getItem('bootinfo');
			if (bootInfo) {
				const boot = JSON.parse(bootInfo);
				if (boot && boot.user && boot.user.roles) {
					const roles = boot.user.roles || [];
					return roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
				}
			}
		} catch (e) {
			// Ignore
		}

		// Check window.boot
		if (typeof window !== 'undefined' && window.boot && window.boot.user && window.boot.user.roles) {
			const roles = window.boot.user.roles || [];
			return roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager");
		}

		return false;
	}

	if (!isSalesAgent()) {
		return; // Not a Sales Agent, exit early
	}

	// Disable the app logo link - make it non-clickable but still visible
	function disableAppLogo() {
		// Try multiple selectors to find the app logo link
		const selectors = [
			'a.navbar-brand.navbar-home',
			'a.navbar-brand[href="/app"]',
			'a.navbar-brand[href*="/app"]',
			'a[href="/app"]',
			'a[href="/app/"]',
			'nav a[href="/app"]',
			'nav a[href="/app/"]',
			'header a.navbar-brand',
			'.navbar a.navbar-brand'
		];

		let appLogoLink = null;
		for (const selector of selectors) {
			appLogoLink = document.querySelector(selector);
			if (appLogoLink && appLogoLink.href && appLogoLink.href.includes('/app')) {
				break;
			}
			if (appLogoLink) break;
		}

		if (appLogoLink && appLogoLink.tagName === 'A') {
			// Remove href to make it non-clickable
			appLogoLink.removeAttribute('href');
			// Add cursor style to show it's not clickable
			appLogoLink.style.cursor = 'default';
			appLogoLink.style.pointerEvents = 'none';
			appLogoLink.style.textDecoration = 'none';
			// Prevent any click events (capture phase to catch early)
			appLogoLink.addEventListener('click', function (e) {
				e.preventDefault();
				e.stopPropagation();
				e.stopImmediatePropagation();
				return false;
			}, true);
			// Also prevent on mousedown
			appLogoLink.addEventListener('mousedown', function (e) {
				e.preventDefault();
				e.stopPropagation();
				return false;
			}, true);

			// Add a class to mark it as disabled
			appLogoLink.classList.add('koraflow-logo-disabled');
		}
	}

	// Intercept ALL clicks on the logo link at document level (capture phase)
	// This runs BEFORE Frappe's router handlers
	document.addEventListener('click', function (e) {
		if (!isSalesAgent()) return;

		const target = e.target.closest('a.navbar-brand.navbar-home, a.navbar-brand[href="/app"], a.navbar-brand[href*="/app"]');
		if (target && target.href && target.href.includes('/app')) {
			e.preventDefault();
			e.stopPropagation();
			e.stopImmediatePropagation();
			return false;
		}
	}, true); // Capture phase - runs before Frappe's handlers

	// Try to disable immediately
	if (document.body) {
		disableAppLogo();
	}

	// Also try after DOM is ready (in case navbar loads later)
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', disableAppLogo);
	}

	// Also try after delays to catch dynamically loaded navbars
	setTimeout(disableAppLogo, 100);
	setTimeout(disableAppLogo, 500);
	setTimeout(disableAppLogo, 1000);
	setTimeout(disableAppLogo, 2000);

	// Use MutationObserver to catch when navbar is added dynamically
	if (document.body) {
		const observer = new MutationObserver(function (mutations) {
			disableAppLogo();
		});

		observer.observe(document.body, {
			childList: true,
			subtree: true
		});
	}

	// Override Frappe's router to redirect Sales Agents from /app/build, /app/user-profile to dashboard
	// This runs immediately when frappe is available
	function setupRouterInterception() {
		if (typeof frappe === 'undefined' || !frappe.router) {
			// Wait for frappe.router to be available
			setTimeout(setupRouterInterception, 100);
			return;
		}

		const originalRoute = frappe.router.route;
		if (originalRoute && !originalRoute._koraflow_wrapped) {
			frappe.router.route = function (path) {
				if (isSalesAgent() && (path === '/app' || path === '/app/' || path.startsWith('/app/build') || path.startsWith('/app/home') || path.startsWith('/app/user-profile'))) {
					// Redirect to dashboard instead of blocking
					if (frappe.set_route) {
						window.location.href = '/sales_agent_dashboard';
					} else {
						window.location.replace('/sales_agent_dashboard');
					}
					return; // Block original navigation
				}
				return originalRoute.apply(this, arguments);
			};
			frappe.router.route._koraflow_wrapped = true;
		}

		const originalSetRoute = frappe.set_route;
		if (originalSetRoute && !originalSetRoute._koraflow_wrapped) {
			frappe.set_route = function () {
				const args = Array.from(arguments);
				if (isSalesAgent() && args.length > 0) {
					const route = args[0];
					if (route === '/app' || route === '/app/' || route === 'app' || route === 'build' || route === 'home' || route === 'user-profile' ||
						route.startsWith('/app/build') || route.startsWith('/app/home') || route.startsWith('/app/user-profile')) {
						// Redirect to dashboard instead of blocking
						window.location.href = '/sales_agent_dashboard';
						return;
					}
				}
				return originalSetRoute.apply(this, arguments);
			};
			frappe.set_route._koraflow_wrapped = true;
		}
	}

	// Start router interception immediately
	if (typeof frappe !== 'undefined') {
		setupRouterInterception();
	} else {
		// Wait for frappe to load
		var frappeWaitInterval = setInterval(function () {
			if (typeof frappe !== 'undefined') {
				clearInterval(frappeWaitInterval);
				setupRouterInterception();
			}
		}, 50);
		setTimeout(function () {
			clearInterval(frappeWaitInterval);
		}, 5000);
	}
})();

// Apply branding on page load
// Wait for frappe to be available, with fallback
(function () {
	function initBranding() {
		if (typeof frappe === 'undefined') {
			// Wait for frappe to load
			setTimeout(initBranding, 100);
			return;
		}

		if (typeof frappe.ready === 'function') {
			frappe.ready(function () {
				runBrandingCode();
			});
		} else {
			// Fallback if frappe.ready is not available
			if (document.readyState === 'loading') {
				document.addEventListener('DOMContentLoaded', runBrandingCode);
			} else {
				runBrandingCode();
			}
		}
	}

	function runBrandingCode() {
		// Apply branding to page title
		if (document.title) {
			document.title = koraflow.applyBranding(document.title);
		}

		// Apply branding to workspace labels
		frappe.call({
			method: 'koraflow_core.branding.get_branding_info',
			callback: function (r) {
				if (r.message) {
					// Update branding map with server-side values
					if (r.message.branding_map) {
						Object.assign(koraflow.branding, r.message.branding_map);
					}
				}
			}
		});

		// Override get_default_route for Sales Agents and check current route
		if (frappe.boot && frappe.boot.user) {
			const roles = frappe.boot.user.roles || [];
			if (roles.includes("Sales Agent") && !roles.includes("Sales Agent Manager") && !roles.includes("System Manager")) {
				// Override get_default_route to return custom dashboard
				if (frappe.router && frappe.router.get_default_route) {
					const originalGetDefaultRoute = frappe.router.get_default_route;
					frappe.router.get_default_route = function () {
						return "/sales_agent_dashboard";
					};
				}

				// Function to check and redirect
				function checkRouteAndRedirect() {
					if (frappe.get_route) {
						const route = frappe.get_route();
						const path = window.location.pathname;
						// Check if we're on /app, /app/home, /app/build, /app/user-profile, or workspace route
						if (route.length === 0 ||
							(route.length === 1 && (route[0] === "Workspaces" || route[0] === "" || route[0] === "home" || route[0] === "build" || route[0] === "user-profile")) ||
							path === "/app" ||
							path === "/app/home" ||
							path === "/app/build" ||
							path === "/app/user-profile" ||
							path === "/app/sales-agent-dashboard" ||
							path.startsWith("/app/sales-agent-dashboard")) {
							if (frappe.set_route) {
								window.location.href = "/sales_agent_dashboard";
								return true;
							}
						}
					}
					return false;
				}

				// Check current route on page load and redirect if needed
				setTimeout(checkRouteAndRedirect, 100);
				setTimeout(checkRouteAndRedirect, 300);
				setTimeout(checkRouteAndRedirect, 500);

				// Also intercept route changes
				if (frappe.router && frappe.router.on) {
					frappe.router.on('change', function () {
						setTimeout(checkRouteAndRedirect, 50);
					});
				}
			}
		}
	}

	// Start initialization
	initBranding();
})();

// Module management
koraflow.modules = {
	toggle: function (module_name, enable, callback) {
		frappe.call({
			method: 'koraflow_core.module_registry.toggle_module',
			args: {
				module_name: module_name,
				enable: enable
			},
			callback: function (r) {
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

	getStatus: function (callback) {
		frappe.call({
			method: 'koraflow_core.module_registry.get_all_modules_status',
			callback: function (r) {
				if (callback) callback(r.message);
			}
		});
	}
};



