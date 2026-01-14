/**
 * Courier Guy Dashboard
 * Fetches real-time data from Courier Guy API and displays it
 * Version: 2.0 - Fixed null route errors
 */

// Wrap everything in IIFE to ensure proper initialization
(function () {
	'use strict';

	// Wait for dependencies and initialize
	function initDashboard() {
		if (typeof frappe === 'undefined') {
			setTimeout(initDashboard, 100);
			return;
		}

		// Create namespace
		frappe.provide('koraflow_core.courier_guy');

		if (typeof koraflow_core === 'undefined' || typeof koraflow_core.courier_guy === 'undefined') {
			setTimeout(initDashboard, 100);
			return;
		}

		// Define Dashboard class if not already defined
		if (!koraflow_core.courier_guy.Dashboard) {
			koraflow_core.courier_guy.Dashboard = class CourierGuyDashboard {
				constructor() {
					this.currentPage = 1;
					this.itemsPerPage = 50;
					this.allShipments = [];
					this.waybill_dialog = null;
					this.init();
				}

				init() {
					this.setup_custom_block();
				}

				setup_custom_block() {
					// Helper function to safely get route
					const getRoute = () => {
						try {
							// Check if frappe exists and has get_route as a function
							if (typeof frappe === 'undefined') {
								return null;
							}
							if (!frappe.get_route || typeof frappe.get_route !== 'function') {
								return null;
							}

							// Call get_route safely
							let route;
							try {
								route = frappe.get_route();
							} catch (callError) {
								// get_route itself threw an error
								return null;
							}

							// Ensure route is an array with at least 2 elements
							if (!route || !Array.isArray(route) || route.length < 2) {
								return null;
							}
							return route;
						} catch (e) {
							// Silently fail - route not available yet
							return null;
						}
					};

					// Helper to check if we're on Courier Guy workspace
					const isCourierGuyWorkspace = () => {
						try {
							// Get pathname early for use in multiple methods
							const pathname = window.location.pathname.toLowerCase();

							// Method 1: Check route
							const route = getRoute();
							if (route && Array.isArray(route) && route.length >= 2) {
								const routeStr = route.map(r => String(r).toLowerCase().trim()).join(',');
								const routeLower = routeStr.toLowerCase();
								const hasWorkspace = routeLower.includes('workspace');
								const hasCourierGuy = (routeLower.includes('courier') && routeLower.includes('guy')) ||
									routeLower.includes('courier-guy') || routeLower.includes('courierguy');

								// Also check individual route parts
								const routeParts = route.map(r => String(r).toLowerCase().trim());
								const hasCourierGuyInParts = routeParts.some(part =>
									(part.includes('courier') && part.includes('guy')) ||
									part === 'courier-guy' || part === 'courierguy' || part === 'courier guy'
								);

								if (hasWorkspace && (hasCourierGuy || hasCourierGuyInParts)) {
									console.log('Courier Guy Dashboard: ✅ Matched workspace route!', route);
									return true;
								}
							}

							// Method 2: Check URL
							const url = window.location.href.toLowerCase();
							// Check for workspace URL or direct /app/courier-guy URL
							if ((url.includes('workspace') || pathname.includes('/app/courier-guy') || pathname.includes('/app/courier_guy')) &&
								(url.includes('courier') || url.includes('courier-guy') || pathname.includes('courier'))) {
								console.log('Courier Guy Dashboard: ✅ Matched workspace URL!', url, pathname);
								return true;
							}

							// Method 3: Check page title or workspace name in DOM
							const pageTitle = document.title.toLowerCase();
							const workspaceName = document.querySelector('.workspace-name, [data-workspace-name]');
							if (pageTitle.includes('courier guy') ||
								(workspaceName && workspaceName.textContent.toLowerCase().includes('courier guy'))) {
								console.log('Courier Guy Dashboard: ✅ Matched workspace name in DOM!');
								return true;
							}

							// Method 4: Check if we're on a workspace page and look for Courier Guy content
							const workspaceContent = document.querySelector('.layout-main-section');
							if (workspaceContent) {
								const contentText = workspaceContent.textContent.toLowerCase();
								// Check for specific Courier Guy content
								if (contentText.includes('courier guy dashboard') ||
									contentText.includes('courier guy settings') ||
									contentText.includes('courier guy') ||
									contentText.includes('waybills') ||
									contentText.includes('waybill') ||
									// Check for page title
									document.title.toLowerCase().includes('courier guy')) {
									console.log('Courier Guy Dashboard: ✅ Matched workspace content!', contentText.substring(0, 100));
									return true;
								}
							}

							// Method 5: Check pathname directly (most reliable for /app/courier-guy)
							if (pathname.includes('/app/courier-guy') || pathname.includes('/app/courier_guy')) {
								console.log('Courier Guy Dashboard: ✅ Matched pathname!', pathname);
								return true;
							}

							return false;
						} catch (e) {
							console.log('Courier Guy Dashboard: Error checking workspace:', e);
							return false;
						}
					};

					// Wait for frappe.router to be available
					const setupRouter = () => {
						if (typeof frappe !== 'undefined' && frappe.router && typeof frappe.router.on === 'function') {
							// Wait for workspace to load
							frappe.router.on('change', () => {
								if (isCourierGuyWorkspace()) {
									setTimeout(() => this.load_dashboard_data(), 1000);
								}
							});
						} else {
							// Retry if router not ready
							setTimeout(setupRouter, 100);
						}
					};

					// Only setup router if frappe is available
					if (typeof frappe !== 'undefined') {
						setupRouter();
					}

					// Also load if already on the page (with delay to ensure frappe is ready)
					setTimeout(() => {
						console.log('Courier Guy Dashboard: Checking if on workspace...');
						if (isCourierGuyWorkspace()) {
							console.log('Courier Guy Dashboard: On Courier Guy workspace, loading dashboard...');
							setTimeout(() => this.load_dashboard_data(), 2000);
						} else {
							console.log('Courier Guy Dashboard: Not on Courier Guy workspace yet');
						}
					}, 500);

					// Listen for workspace content updates
					$(document).on('workspace-rendered', () => {
						if (isCourierGuyWorkspace()) {
							setTimeout(() => this.load_dashboard_data(), 1000);
						}
					});

					// Also try on DOM ready and after a delay
					$(document).ready(() => {
						setTimeout(() => {
							if (isCourierGuyWorkspace()) {
								setTimeout(() => this.load_dashboard_data(), 2500);
							}
						}, 1000);
					});

					// Periodic check (as fallback) - try loading immediately and then periodically
					// Try immediate load with multiple attempts
					const tryLoad = () => {
						// Check if we're on a workspace page (any workspace)
						const isWorkspacePage = window.location.pathname.includes('/app/') &&
							(document.querySelector('.layout-main-section') ||
								document.querySelector('.workspace-content') ||
								document.querySelector('#page-Workspaces'));

						// Check if content suggests Courier Guy workspace
						const hasCourierGuyContent = document.body.textContent.toLowerCase().includes('courier guy') ||
							document.body.textContent.toLowerCase().includes('waybill');

						if ((isCourierGuyWorkspace() || (isWorkspacePage && hasCourierGuyContent)) &&
							!document.querySelector('.courier-guy-api-dashboard')) {
							console.log('Courier Guy Dashboard: Attempting to load dashboard...');
							this.load_dashboard_data();
						}
					};

					// Try multiple times with increasing delays
					setTimeout(tryLoad, 1000);
					setTimeout(tryLoad, 3000);
					setTimeout(tryLoad, 5000);
					setTimeout(tryLoad, 8000);
					setTimeout(tryLoad, 12000);

					// Then periodic checks every 10 seconds
					setInterval(tryLoad, 10000);

					// Also try loading immediately if we can detect Courier Guy content
					setTimeout(() => {
						const layoutSection = document.querySelector('.layout-main-section');
						const pathname = window.location.pathname.toLowerCase();
						const pageTitle = document.title.toLowerCase();

						// Multiple checks to ensure we trigger
						if (layoutSection && (
							layoutSection.textContent.toLowerCase().includes('courier guy') ||
							pathname.includes('/app/courier-guy') ||
							pathname.includes('/app/courier_guy') ||
							pageTitle.includes('courier guy')
						)) {
							console.log('Courier Guy Dashboard: Immediate load triggered by content/URL detection');
							this.load_dashboard_data();
						}
					}, 500);

					// Additional aggressive check - just check URL pattern
					setTimeout(() => {
						const pathname = window.location.pathname.toLowerCase();
						if (pathname.includes('courier-guy') || pathname.includes('courier_guy')) {
							console.log('Courier Guy Dashboard: Aggressive URL check - loading dashboard');
							if (!document.querySelector('.courier-guy-api-dashboard')) {
								this.load_dashboard_data();
							}
						}
					}, 1000);
				}

				async load_dashboard_data() {
					console.log('Courier Guy Dashboard: load_dashboard_data called');

					// Check if dashboard already loaded
					if (document.querySelector('.courier-guy-api-dashboard')) {
						console.log('Courier Guy Dashboard: Already loaded, skipping');
						return;
					}

					// Target the exact element from the DOM path provided: .layout-main-section
					// Try multiple selectors to find the workspace content area
					let dashboard_container =
						document.querySelector('.layout-main-section') ||
						document.querySelector('.col.layout-main-section-wrapper .layout-main-section') ||
						document.querySelector('.codex-editor') ||
						document.querySelector('#editorjs') ||
						document.querySelector('.editor-js-container') ||
						document.querySelector('[data-workspace="Courier Guy"]') ||
						document.querySelector('.workspace-content') ||
						document.querySelector('#page-Workspaces .page-content') ||
						document.querySelector('.page-content') ||
						document.querySelector('.main-section');

					if (!dashboard_container) {
						console.error('Courier Guy Dashboard: Container not found!');
						console.error('  Tried selectors: .layout-main-section, .codex-editor, #editorjs, etc.');
						console.error('  Available elements:', {
							layoutMainSection: !!document.querySelector('.layout-main-section'),
							codexEditor: !!document.querySelector('.codex-editor'),
							editorJs: !!document.querySelector('#editorjs'),
							pageContent: !!document.querySelector('.page-content'),
							body: !!document.querySelector('#body')
						});
						console.log('Courier Guy Dashboard: Retrying in 1 second...');
						setTimeout(() => this.load_dashboard_data(), 1000);
						return;
					}

					console.log('Courier Guy Dashboard: Found container:', dashboard_container.className);
					console.log('Courier Guy Dashboard: Container element:', dashboard_container);

					// Create dashboard container
					const api_dashboard = document.createElement('div');
					api_dashboard.className = 'courier-guy-api-dashboard';

					// Set default date range (last 1 week)
					const today = new Date();
					const oneWeekAgo = new Date(today);
					oneWeekAgo.setDate(today.getDate() - 7);

					const formatDate = (date) => {
						const year = date.getFullYear();
						const month = String(date.getMonth() + 1).padStart(2, '0');
						const day = String(date.getDate()).padStart(2, '0');
						return `${year}-${month}-${day}`;
					};

					// Format dates before using in template (pre-format to avoid scope issues)
					let fromDateStr, toDateStr;
					try {
						fromDateStr = formatDate(oneWeekAgo);
						toDateStr = formatDate(today);
					} catch (e) {
						console.error('Courier Guy Dashboard: Error formatting dates:', e);
						// Fallback to hardcoded dates if formatting fails
						const today_fallback = new Date();
						const oneWeekAgo_fallback = new Date(today_fallback);
						oneWeekAgo_fallback.setDate(today_fallback.getDate() - 7);
						fromDateStr = formatDate(oneWeekAgo_fallback);
						toDateStr = formatDate(today_fallback);
					}

					api_dashboard.innerHTML = `
						<div class="dashboard-header">
							<h4>Courier Guy Live Dashboard</h4>
							<div class="dashboard-actions">
								<button class="btn btn-sm btn-secondary refresh-dashboard" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.refresh(); }">
									<i class="fa fa-refresh"></i> Refresh
								</button>
							</div>
						</div>
						<div class="dashboard-api-warning" style="display: none; margin: 10px 0; padding: 10px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; color: #856404;">
							<i class="fa fa-exclamation-triangle"></i> <span class="warning-message"></span>
						</div>
						<div class="dashboard-filters">
							<div class="filter-row">
								<div class="filter-group">
									<label>From:</label>
									<input type="date" class="form-control date-filter" id="dashboard-from-date" value="${fromDateStr}">
								</div>
								<div class="filter-group">
									<label>To:</label>
									<input type="date" class="form-control date-filter" id="dashboard-to-date" value="${toDateStr}">
								</div>
							</div>
							<div class="filter-row">
								<div class="filter-group">
									<label>Status:</label>
									<select class="form-control" id="filter-status" style="width: 140px;">
										<option value="">All Statuses</option>
										<option value="Delivered">Delivered</option>
										<option value="In Transit">In Transit</option>
										<option value="Collection Request">Collection Request</option>
										<option value="Collected">Collected</option>
										<option value="Out for Delivery">Out for Delivery</option>
										<option value="Failed">Failed</option>
									</select>
								</div>
								<div class="filter-group">
									<label>Contact:</label>
									<input type="text" class="form-control" id="filter-contact" placeholder="Search name..." style="width: 140px;">
								</div>
								<div class="filter-group">
									<label>Cell:</label>
									<input type="text" class="form-control" id="filter-cell" placeholder="Search number..." style="width: 140px;">
								</div>
								<div class="filter-actions">
									<button class="btn btn-sm btn-primary apply-filters" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.applyFilters(); }">
										Apply
									</button>
									<button class="btn btn-sm btn-default clear-filters" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.clearFilters(); }">
										Clear
									</button>
								</div>
							</div>
						</div>
						<div class="dashboard-loading">
							<i class="fa fa-spinner fa-spin"></i> Loading dashboard data...
						</div>
						<div class="dashboard-content" style="display: none;">
							<div class="dashboard-summary">
								<div class="summary-card created">
									<div class="summary-label">Created</div>
									<div class="summary-value" id="summary-created">0</div>
								</div>
								<div class="summary-card collected">
									<div class="summary-label">Collected</div>
									<div class="summary-value" id="summary-collected">0</div>
								</div>
								<div class="summary-card delivered">
									<div class="summary-label">Delivered</div>
									<div class="summary-value" id="summary-delivered">0</div>
								</div>
							</div>

							<div class="dashboard-kpis">
								<div class="kpi-card">
									<div class="kpi-icon">💰</div>
									<div class="kpi-label">Average rate per shipment</div>
									<div class="kpi-value" id="kpi-rate">R 0.00</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⚖️</div>
									<div class="kpi-label">Average charged weight</div>
									<div class="kpi-value" id="kpi-weight">0.00 kg</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⏱️</div>
									<div class="kpi-label">Average collection time</div>
									<div class="kpi-value" id="kpi-collection">0.00 days</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⏱️</div>
									<div class="kpi-label">Average delivery time</div>
									<div class="kpi-value" id="kpi-delivery">0.00 days</div>
								</div>
							</div>
							<div class="dashboard-shipments">
								<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
									<h5 style="margin: 0;">Shipments <span id="shipments-count-badge" class="badge badge-secondary" style="margin-left: 10px;"></span></h5>
									<div class="pagination-controls" style="display: none;">
										<button class="btn btn-sm btn-default" id="prev-page" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.prevPage(); }">
											<i class="fa fa-chevron-left"></i> Previous
										</button>
										<span style="margin: 0 15px;" id="page-info">Page 1</span>
										<button class="btn btn-sm btn-default" id="next-page" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.nextPage(); }">
											Next <i class="fa fa-chevron-right"></i>
										</button>
									</div>
								</div>
								<div class="shipments-table-container">
									<table class="table table-bordered shipments-table">
										<thead>
											<tr>
												<th>Waybill No.</th>
												<th>Status</th>
												<th>Service</th>
												<th>Collection Address</th>
												<th>Created</th>
												<th>Delivery Address</th>
											</tr>
										</thead>
										<tbody id="shipments-tbody">
										</tbody>
									</table>
								</div>
							</div>
						</div>
						<div class="dashboard-error" style="display: none;"></div>
					`;

					// Insert at the top of the workspace content
					// The dashboard_container should be .layout-main-section based on the DOM path
					// Try to insert after any existing headers or at the very beginning
					const firstHeader = dashboard_container.querySelector('h1, h2, h3, h4, .header, [data-type="header"], .ce-block[data-type="header"]');
					if (firstHeader) {
						// Find the parent block or insert after the header's parent
						const headerParent = firstHeader.closest('.ce-block, .workspace-block') || firstHeader.parentElement;
						if (headerParent && headerParent.nextSibling) {
							headerParent.parentElement.insertBefore(api_dashboard, headerParent.nextSibling);
							console.log('Courier Guy Dashboard: Inserted after header block');
						} else if (headerParent) {
							headerParent.parentElement.insertBefore(api_dashboard, headerParent);
							console.log('Courier Guy Dashboard: Inserted before header block');
						} else {
							dashboard_container.insertBefore(api_dashboard, dashboard_container.firstChild);
							console.log('Courier Guy Dashboard: Inserted at beginning (header found but no parent)');
						}
					} else if (dashboard_container.firstChild) {
						dashboard_container.insertBefore(api_dashboard, dashboard_container.firstChild);
						console.log('Courier Guy Dashboard: Inserted before first child of', dashboard_container.className);
					} else {
						dashboard_container.appendChild(api_dashboard);
						console.log('Courier Guy Dashboard: Appended to', dashboard_container.className);
					}

					console.log('Courier Guy Dashboard: Dashboard inserted successfully into', dashboard_container.className);

					// Load data
					await this.fetch_dashboard_data();
				}

				async fetch_dashboard_data() {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						console.error('Courier Guy Dashboard: Dashboard container not found');
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');
					const error = dashboard.querySelector('.dashboard-error');

					if (!loading || !content || !error) {
						console.error('Courier Guy Dashboard: Dashboard elements not found', { loading, content, error });
						return;
					}

					try {
						loading.style.display = 'block';
						content.style.display = 'none';
						error.style.display = 'none';

						// Get date filters
						const fromDate = dashboard.querySelector('#dashboard-from-date')?.value || null;
						const toDate = dashboard.querySelector('#dashboard-to-date')?.value || null;

						// Fetch from Courier Guy API
						frappe.call({
							method: 'koraflow_core.api.courier_guy_dashboard.get_courier_guy_dashboard_data',
							args: {
								from_date: fromDate,
								to_date: toDate
							},
							callback: (r) => {
								console.log('Courier Guy Dashboard: API response raw', r);
								if (r && r.message && r.message.success) {
									const data = r.message.data || {};
									console.log('Courier Guy Dashboard: Data received', data);
									console.log('Courier Guy Dashboard: Source', data.source);
									console.log('Courier Guy Dashboard: Summary', data.summary);
									console.log('Courier Guy Dashboard: Stats', data.stats);
									console.log('Courier Guy Dashboard: Shipments count', data.shipments?.length || 0);

									// Check for API warning (network connectivity issues)
									if (data.api_warning) {
										console.warn('Courier Guy Dashboard: API Warning:', data.api_warning);
										// Show warning but still render dashboard with local data
										this.show_api_warning(data.api_warning);
									}

									// Ensure stats object exists
									if (!data.stats && data.summary) {
										data.stats = {
											total_shipments: data.summary.created || 0,
											delivered: data.summary.delivered || 0,
											in_transit: 0,
											pending: 0,
											failed: 0
										};
									}

									this.render_dashboard(data);
								} else {
									const errorMsg = r?.message?.error || r?.message || 'Failed to load dashboard data';
									console.error('Courier Guy Dashboard: API error', errorMsg);
									this.show_error(errorMsg);
								}
							},
							error: (r) => {
								console.error('Courier Guy Dashboard: API call failed', r);
								this.show_error(r?.message || r?.exc || 'Error connecting to Courier Guy API');
							}
						});

					} catch (e) {
						console.error('Courier Guy Dashboard: Exception', e);
						this.show_error(e.message || 'Unknown error occurred');
					}
				}

				applyFilters() {
					this.fetch_dashboard_data();
				}

				render_dashboard(data) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						console.error('Courier Guy Dashboard: Dashboard container not found for rendering');
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');

					if (!loading || !content) {
						console.error('Courier Guy Dashboard: Dashboard elements not found for rendering');
						return;
					}

					loading.style.display = 'none';
					content.style.display = 'block';

					// Ensure stats are visible even if 0
					console.log('Courier Guy Dashboard: Rendering dashboard with data:', data);
					console.log('Courier Guy Dashboard: Summary:', data.summary);
					console.log('Courier Guy Dashboard: Stats:', data.stats);

					// Render summary cards
					const summary = data.summary || {};
					const stats = data.stats || {};
					const summaryCreated = dashboard.querySelector('#summary-created');
					const summaryCollected = dashboard.querySelector('#summary-collected');
					const summaryDelivered = dashboard.querySelector('#summary-delivered');

					// Use stats if available, otherwise fall back to summary
					const createdValue = stats.total_shipments !== undefined ? stats.total_shipments : (summary.created || 0);
					const collectedValue = summary.collected || 0;
					const deliveredValue = stats.delivered !== undefined ? stats.delivered : (summary.delivered || 0);

					if (summaryCreated) {
						summaryCreated.textContent = createdValue;
						console.log('Courier Guy Dashboard: Set summary-created to', createdValue);
					}
					if (summaryCollected) {
						summaryCollected.textContent = collectedValue;
						console.log('Courier Guy Dashboard: Set summary-collected to', collectedValue);
					}
					if (summaryDelivered) {
						summaryDelivered.textContent = deliveredValue;
						console.log('Courier Guy Dashboard: Set summary-delivered to', deliveredValue);
					}

					// Render KPIs
					const kpis = data.kpis || {};
					const kpiRate = dashboard.querySelector('#kpi-rate');
					const kpiWeight = dashboard.querySelector('#kpi-weight');
					const kpiCollection = dashboard.querySelector('#kpi-collection');
					const kpiDelivery = dashboard.querySelector('#kpi-delivery');

					if (kpiRate) kpiRate.textContent = `R ${(kpis.avg_rate || 0).toFixed(2)}`;
					if (kpiWeight) kpiWeight.textContent = `${(kpis.avg_weight || 0).toFixed(2)} kg`;
					if (kpiCollection) kpiCollection.textContent = `${(kpis.avg_collection_time || 0).toFixed(2)} days`;
					if (kpiDelivery) kpiDelivery.textContent = `${(kpis.avg_delivery_time || 0).toFixed(2)} days`;

					// Store all shipments and initialize filtered list
					this.allShipments = data.shipments || [];
					this.filteredShipments = [...this.allShipments];
					this.currentPage = 1;

					// Render shipments table with pagination
					console.log('Courier Guy Dashboard: Rendering shipments', this.allShipments);
					this.renderPaginatedShipments();

					// Update shipments count badge
					const totalCount = this.filteredShipments.length;
					const countBadge = dashboard.querySelector('#shipments-count-badge');
					if (countBadge) {
						countBadge.textContent = `${totalCount}`;
						countBadge.className = 'badge badge-secondary';
					}
				}

				renderPaginatedShipments() {
					// Use filtered shipments if available, otherwise all
					const source = this.filteredShipments || this.allShipments || [];
					const startIdx = (this.currentPage - 1) * this.itemsPerPage;
					const endIdx = startIdx + this.itemsPerPage;
					const paginatedShipments = source.slice(startIdx, endIdx);

					this.render_shipments_table(paginatedShipments);
					this.updatePaginationControls();
				}

				updatePaginationControls() {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) return;

					const paginationControls = dashboard.querySelector('.pagination-controls');
					const pageInfo = dashboard.querySelector('#page-info');
					const prevBtn = dashboard.querySelector('#prev-page');
					const nextBtn = dashboard.querySelector('#next-page');

					if (!paginationControls) return;

					const source = this.filteredShipments || this.allShipments || [];
					const totalPages = Math.ceil(source.length / this.itemsPerPage);

					// Show pagination only if there are multiple pages
					if (totalPages > 1) {
						paginationControls.style.display = 'block';
						if (pageInfo) {
							pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
						}
						if (prevBtn) {
							prevBtn.disabled = this.currentPage === 1;
						}
						if (nextBtn) {
							nextBtn.disabled = this.currentPage === totalPages;
						}
					} else {
						paginationControls.style.display = 'none';
					}
				}

				prevPage() {
					if (this.currentPage > 1) {
						this.currentPage--;
						this.renderPaginatedShipments();
					}
				}

				nextPage() {
					const source = this.filteredShipments || this.allShipments || [];
					const totalPages = Math.ceil(source.length / this.itemsPerPage);
					if (this.currentPage < totalPages) {
						this.currentPage++;
						this.renderPaginatedShipments();
					}
				}

				render_shipments_chart(chartData) {
					// Chart rendering removed - charts are no longer displayed
					return;
				}

				render_service_level_chart(serviceLevels) {
					// Chart rendering removed - charts are no longer displayed
					return;

				}

				render_shipments_table(shipments) {
					console.log('Courier Guy Dashboard: render_shipments_table called with', shipments);
					const tbody = document.querySelector('.courier-guy-api-dashboard #shipments-tbody') ||
						document.getElementById('shipments-tbody');
					if (!tbody) {
						console.warn('Courier Guy Dashboard: Shipments table body not found');
						return;
					}

					if (!shipments || shipments.length === 0) {
						console.log('Courier Guy Dashboard: No shipments to display');
						tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No shipments found for the selected period.</td></tr>';
						return;
					}

					tbody.innerHTML = shipments.map(shipment => `
						<tr>
							<td><a class="waybill-link" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.openWaybillModal('${shipment.waybill_number || shipment.tracking_number || ''}'); }">${shipment.waybill_number || shipment.name || '-'}</a></td>
							<td><span class="badge badge-${this.get_status_color(shipment.status)}">${shipment.status || '-'}</span></td>
							<td>${shipment.service || shipment.service_type || 'N/A'}</td>
							<td>${this.format_address(shipment.collection_address) || '-'}</td>
							<td>${shipment.created || shipment.date || '-'}</td>
							<td>${this.format_address(shipment.delivery_address) || '-'}</td>
						</tr>
					`).join('');
				}

				format_address(address) {
					if (!address) return '';
					// If address is a string, return it as-is
					if (typeof address === 'string') {
						// Truncate long addresses
						return address.length > 50 ? address.substring(0, 47) + '...' : address;
					}
					// If address is an object, format it
					if (typeof address === 'object') {
						const parts = [];
						if (address.address_line1) parts.push(address.address_line1);
						if (address.suburb) parts.push(address.suburb);
						if (address.city) parts.push(address.city);
						return parts.join(', ') || '';
					}
					return '';
				}

				get_status_color(status) {
					const colors = {
						'Delivered': 'success',
						'In Transit': 'primary',
						'Pending': 'warning',
						'Failed': 'danger',
						'Collection Request': 'warning',
						'Collection assigned': 'warning',
						'At Hub': 'secondary',
						'Collected': 'info',
						'Out for Delivery': 'primary'
					};
					return colors[status] || 'secondary';
				}

				show_api_warning(message) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) return;

					const warningDiv = dashboard.querySelector('.dashboard-api-warning');
					const warningMsg = dashboard.querySelector('.dashboard-api-warning .warning-message');

					if (warningDiv && warningMsg) {
						warningMsg.textContent = message;
						warningDiv.style.display = 'block';
					}
				}

				show_error(message) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						console.error('Courier Guy Dashboard: Dashboard container not found for error display');
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');
					const error = dashboard.querySelector('.dashboard-error');

					if (!loading || !content || !error) {
						console.error('Courier Guy Dashboard: Dashboard elements not found for error display');
						return;
					}

					loading.style.display = 'none';
					content.style.display = 'none';
					error.style.display = 'block';
					error.innerHTML = `
						<div class="alert alert-danger">
							<strong>Error:</strong> ${message}
							<br><small>Make sure Courier Guy Settings are configured correctly.</small>
						</div>
					`;
				}

				refresh() {
					this.fetch_dashboard_data();
				}

				applyFilters() {
					const statusFilter = document.getElementById('filter-status')?.value;
					const contactFilter = document.getElementById('filter-contact')?.value?.toLowerCase();
					const cellFilter = document.getElementById('filter-cell')?.value;

					console.log('Applying filters:', { statusFilter, contactFilter, cellFilter });
					if (this.allShipments.length > 0) {
						console.log('Sample row data:', this.allShipments[0]);
						console.log('Sample contact info:', {
							coll_name_field: this.allShipments[0].collection_contact_name,
							del_name_field: this.allShipments[0].delivery_contact_name,
							coll_obj: this.allShipments[0].collection_address,
							del_obj: this.allShipments[0].delivery_address
						});
					}

					// If no filters, reset
					if (!statusFilter && !contactFilter && !cellFilter) {
						this.clearFilters();
						return;
					}

					this.filteredShipments = this.allShipments.filter(row => {
						let match = true;

						// Status filter
						if (statusFilter) {
							const rowStatus = String(row.status || '').toLowerCase().replace(/-/g, ' ').trim();
							const filterValue = String(statusFilter).toLowerCase().replace(/-/g, ' ').trim();

							if (rowStatus !== filterValue) {
								// Special case: "collection assigned" and "collection request" are treated as same
								const isCollection1 = rowStatus === 'collection assigned' || rowStatus === 'collection request';
								const isCollection2 = filterValue === 'collection assigned' || filterValue === 'collection request';

								if (!(isCollection1 && isCollection2)) {
									match = false;
								}
							}
						}

						// Contact filter (check both collection and delivery)
						if (match && contactFilter) {
							const collName = (String(row.collection_address?.contact_name || row.collection_contact_name || '')).toLowerCase();
							const delName = (String(row.delivery_address?.contact_name || row.delivery_contact_name || '')).toLowerCase();

							// Debug first mismatch
							if (contactFilter === 'debug') {
								console.log('Checking contact:', { collName, delName, match: collName.includes(contactFilter) || delName.includes(contactFilter) });
							}

							if (!(collName.includes(contactFilter) || delName.includes(contactFilter))) {
								match = false;
							}
						}

						// Cell filter (check both collection and delivery)
						if (match && cellFilter) {
							const collNums = String(row.collection_address?.contact_phone || row.collection_contact_number || '');
							const delNums = String(row.delivery_address?.contact_phone || row.delivery_contact_number || '');
							if (!(collNums.includes(cellFilter) || delNums.includes(cellFilter))) {
								match = false;
							}
						}

						return match;
					});

					console.log('Filtered result count:', this.filteredShipments.length);

					this.currentPage = 1;
					this.renderPaginatedShipments();

					// Update badge
					const countBadge = document.querySelector('#shipments-count-badge');
					if (countBadge) {
						countBadge.textContent = `${this.filteredShipments.length} (filtered)`;
					}
				}

				clearFilters() {
					// Clear input fields
					if (document.getElementById('filter-status')) document.getElementById('filter-status').value = '';
					if (document.getElementById('filter-contact')) document.getElementById('filter-contact').value = '';
					if (document.getElementById('filter-cell')) document.getElementById('filter-cell').value = '';

					// Reset data
					this.filteredShipments = [...this.allShipments];
					this.currentPage = 1;
					this.renderPaginatedShipments();

					// Update badge
					const countBadge = document.querySelector('#shipments-count-badge');
					if (countBadge) {
						countBadge.textContent = `${this.filteredShipments.length}`;
					}
				}

				async openWaybillModal(waybillNumber) {
					if (!waybillNumber || waybillNumber === 'N/A') return;

					// Create dialog if it doesn't exist
					if (!this.waybill_dialog) {
						this.waybill_dialog = new frappe.ui.Dialog({
							title: __('Waybill Details'),
							fields: [
								{
									fieldtype: 'HTML',
									fieldname: 'details_html',
									options: '<div id="wb-dialog-body"></div>'
								}
							],
							primary_action_label: __('Close'),
							primary_action: () => this.waybill_dialog.hide()
						});
					}

					this.waybill_dialog.set_title(__('Waybill: {0}', [waybillNumber]));
					this.waybill_dialog.show();

					// Show loading state
					const dialogBody = this.waybill_dialog.get_field('details_html').$wrapper.find('#wb-dialog-body');
					dialogBody.html(`
						<div class="text-center" style="padding: 40px; color: #8d99a6;">
							<i class="fa fa-spinner fa-spin" style="font-size: 24px; margin-bottom: 10px;"></i>
							<div>Loading waybill details...</div>
						</div>
					`);

					// Check for local data first (case-insensitive search)
					const wbUpper = waybillNumber.toUpperCase();
					const localData = this.allShipments.find(s =>
						(s.waybill_number || '').toUpperCase() === wbUpper ||
						(s.tracking_number || '').toUpperCase() === wbUpper ||
						(s.short_tracking_reference || '').toUpperCase() === wbUpper ||
						(s.custom_tracking_reference || '').toUpperCase() === wbUpper
					);

					if (localData) {
						console.log('Courier Guy Modal: Using cached local data for', waybillNumber, localData);
						this.renderWaybillDetails(localData);
					}


					try {
						const response = await frappe.call({
							method: 'koraflow_core.api.courier_guy_dashboard.get_waybill_details',
							args: { waybill_number: waybillNumber }
						});

						if (response.message && response.message.success) {
							let apiData = response.message.data;

							// Merge with local data - preserve local address/contact if API doesn't have them
							if (localData) {
								// Preserve delivery address from local data if API returned empty/missing
								if (!apiData.delivery_address || (typeof apiData.delivery_address === 'object' && Object.keys(apiData.delivery_address).length === 0)) {
									apiData.delivery_address = localData.delivery_address;
								}
								if (!apiData.collection_address || (typeof apiData.collection_address === 'object' && Object.keys(apiData.collection_address).length === 0)) {
									apiData.collection_address = localData.collection_address;
								}
								// Preserve contact info if API lacks it
								if (!apiData.delivery_contact_name) apiData.delivery_contact_name = localData.delivery_contact_name;
								if (!apiData.delivery_contact_number) apiData.delivery_contact_number = localData.delivery_contact_number;
								if (!apiData.delivery_email) apiData.delivery_email = localData.delivery_email;
								if (!apiData.collection_contact_name) apiData.collection_contact_name = localData.collection_contact_name;
								if (!apiData.collection_contact_number) apiData.collection_contact_number = localData.collection_contact_number;
								// Also preserve other useful local fields
								if (!apiData.service_level && localData.service) apiData.service_level = localData.service;
								console.log('Courier Guy Modal: Merged API data with local data', apiData);
							}

							this.renderWaybillDetails(apiData);
						} else if (!localData) {

							dialogBody.html(`
								<div class="alert alert-danger" style="margin: 20px;">
									${response.message ? response.message.error : __('Waybill not found')}
								</div>
							`);
						}
					} catch (error) {
						console.error('Error fetching waybill details:', error);
						if (!localData) {
							dialogBody.html(`
								<div class="alert alert-danger" style="margin: 20px;">
									${__('An error occurred while fetching details.')}
								</div>
							`);
						}
					}
				}

				renderWaybillDetails(data) {
					if (!this.waybill_dialog) return;
					const dialogBody = this.waybill_dialog.get_field('details_html').$wrapper.find('#wb-dialog-body');
					if (!dialogBody.length) return;

					// Simplified time formatting for vertical layout (placed next to labels)
					const formatTrackerDate = (dateStr) => {
						if (!dateStr) return '';
						try {
							const d = new Date(dateStr);
							if (isNaN(d.getTime())) return '';
							return d.toLocaleString('en-GB', {
								day: '2-digit', month: 'short', year: 'numeric',
								hour: '2-digit', minute: '2-digit', hour12: false
							}).replace(',', '');
						} catch (e) { return ''; }
					};

					const formatDate = (dateStr) => {
						if (!dateStr) return '';
						try {
							const d = new Date(dateStr);
							if (isNaN(d.getTime())) return dateStr;
							return d.toLocaleString('en-GB', {
								day: '2-digit',
								month: 'short',
								year: 'numeric',
								hour: '2-digit',
								minute: '2-digit',
								hour12: false
							}).replace(',', '');
						} catch (e) { return dateStr; }
					};

					// Format addresses
					const formatAddr = (addr) => {
						if (!addr) return 'N/A';
						if (typeof addr === 'string') return addr;
						const lines = [
							addr.street_address || addr.address_line1 || addr.entered_address,
							addr.suburb || addr.local_area,
							addr.city || addr.geo_city,
							addr.postal_code || addr.zip_code,
							addr.country || 'South Africa'
						].filter(Boolean);
						return lines.join('<br>') || 'N/A';
					};

					// Tracking History Logic
					let trackingHistoryHtml = '';
					if (data.tracking_history && data.tracking_history.length > 0) {
						// Sort by date desc - Ship Logic uses 'date' not 'timestamp'
						const sortedHistory = [...data.tracking_history].sort((a, b) => {
							const dateA = new Date(a.date || a.timestamp || 0);
							const dateB = new Date(b.date || b.timestamp || 0);
							return dateB - dateA;
						});

						// Group by Date
						let lastDate = null;
						sortedHistory.forEach(event => {
							// Ship Logic uses 'date' field, fallback to 'timestamp'
							const eventDate = event.date || event.timestamp;
							if (!eventDate) return;

							const d = new Date(eventDate);
							const dateStr = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
							const timeStr = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });

							if (dateStr !== lastDate) {
								if (lastDate !== null) trackingHistoryHtml += `</div>`; // Close previous group
								trackingHistoryHtml += `
									<div class="tracking-date-group" style="margin-bottom: 25px;">
										<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
											<div style="color: #28a745; font-size: 16px;">
												<i class="fa fa-map-marker-alt"></i>
											</div>
											<span style="font-weight: 800; font-size: 15px; color: #000;">${dateStr}</span>
										</div>
								`;
								lastDate = dateStr;
							}

							// Ship Logic uses 'status' and 'message' (not 'description')
							// Format status: 'at-hub' -> 'At hub', 'collection-assigned' -> 'Collection assigned'
							let statusRaw = event.status || 'Update';
							let statusText = statusRaw.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

							// Get detail: prefer message, then location
							let detailText = event.message || event.description || '';
							if (event.location && event.location.trim()) {
								if (detailText) {
									detailText += ` (${event.location})`;
								} else {
									detailText = event.location;
								}
							}

							// If description is same as status, clear detail to avoid duplication
							if (detailText.toLowerCase() === statusText.toLowerCase()) detailText = '';

							trackingHistoryHtml += `
								<div style="display: flex; gap: 20px; margin-bottom: 15px; padding-left: 5px;">
									<div style="font-size: 14px; color: #36414c; width: 45px; text-align: right; flex-shrink: 0; font-weight: 500;">${timeStr}</div>
									<div style="display: flex; flex-direction: column; gap: 3px;">
										<div style="font-size: 14px; font-weight: 800; color: #000;">${statusText}</div>
										${detailText ? `<div style="font-size: 14px; color: #555;">${detailText}</div>` : ''}
									</div>
								</div>
							`;
						});
						if (lastDate) trackingHistoryHtml += `</div>`;
					} else {
						// Fallback if no history but status exists
						trackingHistoryHtml = `<div style="padding: 20px; color: #888;">No detailed tracking history available.</div>`;
					}


					// Collect from logic
					let collectFrom = 'N/A';
					if (data.collection_contact_name) collectFrom = data.collection_contact_name;
					else if (data.collection_address && data.collection_address.suburb) collectFrom = data.collection_address.suburb;
					else if (data.collection_address && data.collection_address.city) collectFrom = data.collection_address.city;

					dialogBody.html(`
						<div class="cg-modal-body" style="padding: 0; background: #fafafa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
							<div style="padding: 20px;">
								<div style="display: flex; gap: 20px; margin-bottom: 20px;">
									<!-- Left Column: Tracking Events -->
									<div class="cg-card" style="flex: 1; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
										<h3 style="font-size: 16px; font-weight: 800; color: #000; margin: 0 0 25px 0;">Tracking events</h3>
										<div class="cg-tracking-timeline">
											${trackingHistoryHtml}
										</div>
									</div>
									
									<!-- Right Column: Shipping Details -->
									<div class="cg-card" style="flex: 1; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
										<h3 style="font-size: 16px; font-weight: 800; color: #000; margin: 0 0 25px 0;">Shipping details</h3>
										
										<div style="display: flex; flex-direction: column; gap: 15px;">
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Waybill no</span>
												<span style="font-size: 14px; font-weight: 700; color: #1976d2;">${data.waybill_number || '-'}</span>
											</div>
											
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Service level</span>
												<span style="font-size: 14px; color: #36414c;">${data.service_level || 'N/A'}</span>
											</div>
											
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Hubs</span>
												<span style="font-size: 14px; color: #36414c; font-weight: 700;">
													${data.from_hub || 'N/A'} <i class="fa fa-arrow-right" style="margin: 0 5px; font-size: 12px;"></i> ${data.to_hub || 'N/A'}
												</span>
											</div>
											
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Collect from</span>
												<span style="font-size: 14px; color: #36414c;">${collectFrom}</span>
											</div>
											
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Expected delivery</span>
												<span style="font-size: 14px; color: #36414c;">${data.delivered_at ? formatDate(data.delivered_at) : (data.estimated_delivery_at ? formatDate(data.estimated_delivery_at) : 'Processing...')}</span>
											</div>
											
											<div style="display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: baseline;">
												<span style="font-size: 14px; font-weight: 700; color: #000;">Number of parcels</span>
												<span style="font-size: 14px; color: #36414c;">${data.parcel_count || 1}</span>
											</div>
										</div>
									</div>
								</div>
								
								<!-- Delivery Section (Full Width) -->
								<div class="cg-card" style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">
									<div style="background: #f8f9fa; padding: 18px 20px; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 15px;">
										<div style="background: #e8f5e9; color: #4caf50; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px;">
											<i class="fa fa-truck"></i>
										</div>
										<span style="font-weight: 700; font-size: 17px; color: #36414c;">Delivery</span>
									</div>
									
									<div style="padding: 25px 30px;">
										<!-- Expected Dates -->
										<div style="margin-bottom: 30px; line-height: 2;">
											<div style="display: flex; gap: 10px;">
												<span style="font-size: 14px; font-weight: 700; color: #36414c; min-width: 180px;">Earliest requested delivery</span>
												<span style="font-size: 14px; color: #36414c;">${data.delivery_min ? formatDate(data.delivery_min) : 'N/A'}</span>
											</div>
											<div style="display: flex; gap: 10px;">
												<span style="font-size: 14px; font-weight: 700; color: #36414c; min-width: 180px;">Expected delivery</span>
												<span style="font-size: 14px; color: #36414c;">${data.delivered_at ? formatDate(data.delivered_at) : (data.estimated_delivery_at ? formatDate(data.estimated_delivery_at) : 'Processing...')}</span>
											</div>
										</div>
										
										<!-- Address -->
										<div style="margin-bottom: 35px;">
											<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
												<div style="background: #ffebee; color: #f44336; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">
													<i class="fa fa-map-marker-alt"></i>
												</div>
												<span style="font-size: 16px; font-weight: 700; color: #36414c;">Address and instructions</span>
											</div>
											<div style="padding-left: 40px; font-size: 14px; font-weight: 700; color: #36414c; line-height: 1.6;">
												${formatAddr(data.delivery_address).split('<br>').map(line => `<div style="margin-bottom: 2px;">${line}</div>`).join('')}
												${typeof data.delivery_address === 'object' && data.delivery_address && (data.delivery_address.suburb || data.delivery_address.city) ? `<div style="margin-top: 5px; color: #36414c;">(${data.delivery_address.suburb || '-'}, ${data.delivery_address.city || '-'})</div>` : ''}
											</div>
										</div>
										
										<!-- Contact -->
										<div>
											<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
												<div style="background: #fffde7; color: #fbc02d; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">
													<i class="fa fa-user"></i>
												</div>
												<span style="font-size: 16px; font-weight: 700; color: #36414c;">Contact details</span>
											</div>
											<div style="padding-left: 40px; font-size: 14px; color: #36414c;">
												<div style="margin-bottom: 10px;">
													<span style="font-weight: 700; width: 140px; display: inline-block;">Name and surname</span>
													<span>${data.delivery_contact_name || 'N/A'}</span>
												</div>
												<div style="margin-bottom: 10px;">
													<span style="font-weight: 700; width: 140px; display: inline-block;">Email address</span>
													<span>${data.delivery_email || '-'}</span>
												</div>
												<div>
													<span style="font-weight: 700; width: 140px; display: inline-block;">Contact number</span>
													<span>${data.delivery_contact_number || 'N/A'}</span>
												</div>
											</div>
										</div>
									</div>
								</div>

							</div>
						</div>
					`);
				}

				// Cleanup charts on destroy
				destroy() {
					if (this.waybill_dialog) {
						this.waybill_dialog.hide();
					}

					if (this.shipmentsChart) {
						this.shipmentsChart.destroy();
					}
					if (this.serviceLevelChart) {
						this.serviceLevelChart.destroy();
					}
				}
			};
		}

		// Initialize dashboard instance
		if (!koraflow_core.courier_guy.dashboard) {
			koraflow_core.courier_guy.dashboard = new koraflow_core.courier_guy.Dashboard();
			console.log('Courier Guy Dashboard: Initialized successfully');
		}

		// Also try direct injection on page load
		$(document).ready(function () {
			setTimeout(function () {
				try {
					if (typeof frappe !== 'undefined' && frappe.get_route && typeof frappe.get_route === 'function') {
						let route;
						try {
							route = frappe.get_route();
						} catch (e) {
							return; // get_route failed, exit early
						}
						if (route && Array.isArray(route) && route.length >= 2) {
							const first = route[0];
							const second = String(route[1] || '').toLowerCase();
							// Check for both "Courier Guy" (space) and "courier-guy" (hyphen) formats
							if (first === 'workspace' && (
								second === 'courier guy' ||
								second === 'courier-guy' ||
								second.includes('courier') && second.includes('guy')
							)) {
								if (!document.querySelector('.courier-guy-api-dashboard')) {
									if (koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) {
										koraflow_core.courier_guy.dashboard.load_dashboard_data();
									}
								}
							}
						}
					}
				} catch (e) {
					console.log('Courier Guy Dashboard: Error checking route', e);
				}
			}, 3000);
		});
	}

	// Start initialization - wait for Frappe to be fully loaded
	const waitForFrappe = () => {
		if (typeof frappe !== 'undefined' && typeof frappe.provide === 'function') {
			initDashboard();
		} else {
			setTimeout(waitForFrappe, 100);
		}
	};

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', waitForFrappe);
	} else {
		// If DOM already loaded, wait for Frappe
		waitForFrappe();
	}

	// Final fallback: Check every 2 seconds if we're on courier-guy page and dashboard isn't loaded
	setInterval(() => {
		const pathname = window.location.pathname.toLowerCase();
		if ((pathname.includes('courier-guy') || pathname.includes('courier_guy')) &&
			!document.querySelector('.courier-guy-api-dashboard')) {
			console.log('Courier Guy Dashboard: Fallback check - attempting to load dashboard');
			if (typeof koraflow_core !== 'undefined' &&
				koraflow_core.courier_guy &&
				koraflow_core.courier_guy.dashboard) {
				koraflow_core.courier_guy.dashboard.load_dashboard_data();
			} else if (typeof frappe !== 'undefined' && typeof frappe.provide === 'function') {
				// Try to initialize if not already done
				waitForFrappe();
			}
		}
	}, 2000);
})();
