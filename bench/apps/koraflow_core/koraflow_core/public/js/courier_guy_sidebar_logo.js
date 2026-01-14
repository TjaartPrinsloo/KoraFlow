// Courier Guy Sidebar Logo
// Adds custom logo to Courier Guy workspace in sidebar

(function() {
	function addCourierGuyLogo() {
		// Find the Courier Guy sidebar item by href or title
		const courierGuyItems = document.querySelectorAll('a.item-anchor[href*="courier-guy"], a.item-anchor[href*="courier_guy"], a.item-anchor[title="Courier Guy"]');
		
		courierGuyItems.forEach(function(courierGuyItem) {
			const iconSpan = courierGuyItem.querySelector('.sidebar-item-icon');
			
			if (iconSpan && !iconSpan.hasAttribute('data-courier-guy-logo')) {
				// Mark as processed
				iconSpan.setAttribute('data-courier-guy-logo', 'true');
				
				// Create logo image element
				const logoImg = document.createElement('img');
				logoImg.src = '/assets/koraflow_core/images/courier_guy_logo.svg';
				logoImg.alt = 'Courier Guy';
				logoImg.className = 'courier-guy-logo';
				logoImg.style.cssText = 'width: 20px; height: 20px; object-fit: contain; display: block;';
				
				// Fallback: if image fails to load, restore original
				logoImg.onerror = function() {
					// Remove the logo and restore original icon
					if (iconSpan.contains(logoImg)) {
						iconSpan.removeChild(logoImg);
					}
					iconSpan.removeAttribute('data-courier-guy-logo');
					// Restore the original icon
					const iconName = iconSpan.getAttribute('item-icon') || 'truck';
					iconSpan.innerHTML = frappe.utils.icon(iconName, 'md');
				};
				
				// Clear existing icon content (including SVG) and add logo
				iconSpan.innerHTML = '';
				iconSpan.appendChild(logoImg);
			}
		});
	}
	
	// Hook into workspace sidebar creation
	if (typeof frappe !== 'undefined') {
		// Override the sidebar_item_container method if workspace is available
		if (frappe.views && frappe.views.Workspace) {
			const originalSidebarItemContainer = frappe.views.Workspace.prototype.sidebar_item_container;
			if (originalSidebarItemContainer) {
				frappe.views.Workspace.prototype.sidebar_item_container = function(item) {
					const $item = originalSidebarItemContainer.call(this, item);
					
					// Check if this is Courier Guy workspace
					if (item.title === 'Courier Guy' || (item.title && item.title.toLowerCase().includes('courier guy'))) {
						// Replace icon with logo after a short delay
						setTimeout(() => {
							const iconSpan = $item.find('.sidebar-item-icon');
							if (iconSpan.length && !iconSpan.attr('data-courier-guy-logo')) {
								iconSpan.attr('data-courier-guy-logo', 'true');
								const logoImg = $('<img>', {
									src: '/assets/koraflow_core/images/courier_guy_logo.svg',
									alt: 'Courier Guy',
									class: 'courier-guy-logo',
									css: {
										width: '20px',
										height: '20px',
										'object-fit': 'contain',
										display: 'block'
									}
								});
								
								logoImg.on('error', function() {
									$(this).remove();
									iconSpan.removeAttr('data-courier-guy-logo');
								});
								
								iconSpan.html(logoImg);
							}
						}, 50);
					}
					
					return $item;
				};
			}
		}
		
		// Also run when DOM is ready
		if (typeof frappe !== 'undefined' && typeof frappe.ready === 'function') {
			frappe.ready(function() {
				addCourierGuyLogo();
				
				// Run multiple times to catch dynamically loaded content
				setTimeout(addCourierGuyLogo, 300);
				setTimeout(addCourierGuyLogo, 800);
				setTimeout(addCourierGuyLogo, 1500);
				setTimeout(addCourierGuyLogo, 3000);
			});
		} else {
			// Fallback if frappe.ready is not available
			if (document.readyState === 'loading') {
				document.addEventListener('DOMContentLoaded', function() {
					addCourierGuyLogo();
					setTimeout(addCourierGuyLogo, 300);
					setTimeout(addCourierGuyLogo, 800);
					setTimeout(addCourierGuyLogo, 1500);
					setTimeout(addCourierGuyLogo, 3000);
				});
			} else {
				addCourierGuyLogo();
				setTimeout(addCourierGuyLogo, 300);
				setTimeout(addCourierGuyLogo, 800);
				setTimeout(addCourierGuyLogo, 1500);
				setTimeout(addCourierGuyLogo, 3000);
			}
		}
	} else {
		// Fallback if frappe is not available
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', function() {
				addCourierGuyLogo();
				setTimeout(addCourierGuyLogo, 500);
				setTimeout(addCourierGuyLogo, 1500);
			});
		} else {
			addCourierGuyLogo();
			setTimeout(addCourierGuyLogo, 500);
			setTimeout(addCourierGuyLogo, 1500);
		}
	}
	
	// Watch for sidebar changes using MutationObserver
	if (typeof MutationObserver !== 'undefined') {
		const observer = new MutationObserver(function(mutations) {
			let shouldCheck = false;
			mutations.forEach(function(mutation) {
				if (mutation.addedNodes.length > 0) {
					shouldCheck = true;
				}
			});
			if (shouldCheck) {
				setTimeout(addCourierGuyLogo, 50);
			}
		});
		
		// Observe sidebar container when available
		function startObserving() {
			const sidebarContainer = document.querySelector('.desk-sidebar, .standard-sidebar-section, .sidebar-menu');
			if (sidebarContainer) {
				observer.observe(sidebarContainer, {
					childList: true,
					subtree: true
				});
			} else {
				setTimeout(startObserving, 500);
			}
		}
		
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', startObserving);
		} else {
			startObserving();
		}
	}
})();
